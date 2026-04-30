"""Spec-driven processing engine with cross-table lookup support."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from linkml_map.transformer.errors import TransformationError
from linkml_map.utils.join_utils import pick_join_key
from linkml_map.utils.lookup_index import LookupIndex

if TYPE_CHECKING:
    from collections.abc import Iterator

    from linkml_runtime import SchemaView

    from linkml_map.datamodel.transformer_model import ClassDerivation
    from linkml_map.loaders.data_loaders import DataLoader
    from linkml_map.transformer.object_transformer import ObjectTransformer

logger = logging.getLogger(__name__)


def _collect_implicit_join_tables(
    class_deriv: ClassDerivation,
    parent_source: str,
    data_loader: DataLoader,
    sv: SchemaView,
) -> list[tuple[str, str]]:
    """Walk nested class_derivations to find cross-table references needing implicit joins.

    :param class_deriv: Top-level class derivation to scan.
    :param parent_source: The parent's populated_from table name.
    :param data_loader: Data loader to check if tables exist.
    :param sv: Source schema view for finding common columns.
    :returns: List of (table_name, join_key) pairs for tables that need registration.
    """
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    def _walk_slots(slot_derivations: dict, current_source: str) -> None:
        for sd in slot_derivations.values():
            if not sd.class_derivations:
                continue
            for nested_cd in sd.class_derivations:
                nested_source = nested_cd.populated_from
                if (
                    nested_source
                    and nested_source != current_source
                    and not nested_cd.joins
                    and nested_source not in seen
                    and nested_source in data_loader
                ):
                    # Find common columns to determine join key
                    join_key = pick_join_key(sv, current_source, nested_source)
                    if join_key:
                        results.append((nested_source, join_key))
                        seen.add(nested_source)
                        logger.info(
                            "Engine: will register %r for implicit join on %r",
                            nested_source, join_key,
                        )
                # Recurse into nested derivation's own slots
                if nested_cd.slot_derivations:
                    _walk_slots(nested_cd.slot_derivations, nested_cd.populated_from or current_source)

    _walk_slots(class_deriv.slot_derivations, parent_source)
    return results


def transform_spec(
    transformer: ObjectTransformer,
    data_loader: DataLoader,
    source_type: str | None = None,
    on_error: Callable[[TransformationError], None] | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Iterate class_derivation blocks and stream transformed rows.

    For each block whose ``populated_from`` names a loadable table, this
    function:

    1. Registers any ``joins`` as secondary tables in a :class:`LookupIndex`.
    2. Discovers nested class_derivations that need implicit cross-table joins
       and registers those tables as well.
    3. Streams primary-table rows through
       :meth:`ObjectTransformer.map_object`.
    4. Drops secondary tables when the block is done.

    :param transformer: A configured :class:`ObjectTransformer`.
    :param data_loader: Loader that can resolve table names to file paths.
    :param source_type: Optional explicit source type override.
    :param on_error: Optional callback for row-level errors. When provided,
        :class:`TransformationError` is caught, enriched with row context,
        and passed to the callback. When ``None`` (default), errors propagate
        immediately (fail-fast).
    :returns: Iterator of transformed row dicts.
    """
    spec = transformer.derived_specification
    if spec is None:
        return

    if transformer.lookup_index is None:
        transformer.lookup_index = LookupIndex()

    for class_deriv in spec.class_derivations:
        table_name = class_deriv.populated_from or class_deriv.name
        if table_name not in data_loader:
            logger.debug("Skipping class_derivation %s: no data found", class_deriv.name)
            continue

        joined_tables: list[str] = []
        try:
            # Register secondary (joined) tables from explicit joins: blocks
            if class_deriv.joins:
                for join_name, join_spec in class_deriv.joins.items():
                    lookup_key = join_spec.lookup_key or join_spec.join_on
                    source_key = join_spec.source_key or join_spec.join_on
                    if not lookup_key or not source_key:
                        msg = f"Join {join_name!r} must specify 'join_on' or both 'source_key' and 'lookup_key'"
                        raise ValueError(msg)
                    join_path = data_loader.get_path(join_name)
                    transformer.lookup_index.register_table(join_name, join_path, lookup_key)
                    joined_tables.append(join_name)

            # Register tables needed for implicit cross-table joins in nested derivations
            implicit_joins = _collect_implicit_join_tables(
                class_deriv, table_name, data_loader, transformer.source_schemaview,
            )
            for implicit_table, join_key in implicit_joins:
                if not transformer.lookup_index.is_registered(implicit_table):
                    join_path = data_loader.get_path(implicit_table)
                    transformer.lookup_index.register_table(implicit_table, join_path, join_key)
                    joined_tables.append(implicit_table)

            # Stream primary table rows
            for row_idx, row in enumerate(data_loader[table_name]):
                try:
                    yield transformer.map_object(
                        row,
                        source_type=source_type or table_name,
                        class_derivation=class_deriv,
                    )
                except TransformationError as err:
                    if on_error is None:
                        raise
                    err.row_index = row_idx
                    err.class_derivation_name = err.class_derivation_name or class_deriv.name
                    on_error(err)
        finally:
            for jt in joined_tables:
                transformer.lookup_index.drop(jt)
