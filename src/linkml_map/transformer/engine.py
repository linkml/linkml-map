"""Spec-driven processing engine with cross-table lookup support."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from linkml_map.transformer.errors import TransformationError
from linkml_map.utils.lookup_index import LookupIndex

if TYPE_CHECKING:
    from collections.abc import Iterator

    from linkml_map.datamodel.transformer_model import ClassDerivation
    from linkml_map.loaders.data_loaders import DataLoader
    from linkml_map.transformer.object_transformer import ObjectTransformer

logger = logging.getLogger(__name__)


def _collect_all_joins(class_deriv: ClassDerivation) -> dict[str, tuple[str, str]]:
    """Collect all join specs from a class derivation and its nested descendants.

    Walks the slot_derivation tree recursively to find joins that were either
    explicitly declared or synthesized during normalization.

    :param class_deriv: Root class derivation to scan.
    :returns: Dict of {table_name: (source_key, lookup_key)} for all joins found.
    """
    result: dict[str, tuple[str, str]] = {}

    def _collect_from(cd: ClassDerivation) -> None:
        if cd.joins:
            for join_name, join_spec in cd.joins.items():
                lookup_key = join_spec.lookup_key or join_spec.join_on
                source_key = join_spec.source_key or join_spec.join_on
                if not lookup_key or not source_key:
                    msg = f"Join {join_name!r} must specify 'join_on' or both 'source_key' and 'lookup_key'"
                    raise ValueError(msg)
                existing = result.get(join_name)
                if existing and existing != (source_key, lookup_key):
                    msg = f"Conflicting join specs for {join_name!r}: {existing} vs ({source_key!r}, {lookup_key!r})"
                    raise ValueError(msg)
                result[join_name] = (source_key, lookup_key)
        for sd in cd.slot_derivations.values():
            if sd.class_derivations:
                for nested_cd in sd.class_derivations:
                    _collect_from(nested_cd)

    _collect_from(class_deriv)
    return result


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

    1. Registers any ``joins`` as secondary tables in a :class:`LookupIndex`,
       including joins synthesized during normalization for implicit cross-table
       references.
    2. Streams primary-table rows through
       :meth:`ObjectTransformer.map_object`.
    3. Drops secondary tables when the block is done.

    **LookupIndex ownership and cleanup:**

    - If ``transformer.lookup_index`` is ``None`` on entry, this function
      creates one, uses it for the duration of iteration, then closes it
      and detaches it (sets ``transformer.lookup_index = None``) when the
      iterator is exhausted, raises, or is closed early. Detachment lets a
      subsequent call on the same transformer create a fresh index instead
      of reusing the now-closed connection.
    - If the caller pre-attached a ``LookupIndex``, this function uses it
      but does **not** close or detach it. Lifecycle is the caller's
      responsibility.

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

    owns_index = transformer.lookup_index is None
    if owns_index:
        transformer.lookup_index = LookupIndex()

    try:
        for class_deriv in spec.class_derivations:
            table_name = class_deriv.populated_from or class_deriv.name
            if table_name not in data_loader:
                logger.debug("Skipping class_derivation %s: no data found", class_deriv.name)
                continue

            joined_tables: list[str] = []
            try:
                # Register all joined tables (explicit + synthesized from normalization).
                # _collect_all_joins walks nested derivations and validates each join spec.
                all_joins = _collect_all_joins(class_deriv)
                for join_name, (_source_key, lookup_key) in all_joins.items():
                    if join_name in data_loader and not transformer.lookup_index.is_registered(join_name):
                        join_path = data_loader.get_path(join_name)
                        transformer.lookup_index.register_table(join_name, join_path, lookup_key)
                        joined_tables.append(join_name)

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
    finally:
        if owns_index:
            # Close the index we created and detach it so a second call on the
            # same transformer reinitializes a fresh one rather than reusing
            # the now-closed connection.
            transformer.lookup_index.close()
            transformer.lookup_index = None
