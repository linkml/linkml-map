"""Spec-driven processing engine with cross-table lookup support."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from linkml_map.transformer.errors import TransformationError
from linkml_map.utils.lookup_index import LookupIndex

if TYPE_CHECKING:
    from collections.abc import Iterator

    from linkml_map.loaders.data_loaders import DataLoader
    from linkml_map.transformer.object_transformer import ObjectTransformer

logger = logging.getLogger(__name__)


def transform_spec(
    transformer: ObjectTransformer,
    data_loader: DataLoader,
    source_type: str | None = None,
    on_error: Callable[[TransformationError], None] | None = None,
    entity: str | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Iterate class_derivation blocks and stream transformed rows.

    For each block whose ``populated_from`` names a loadable table, this
    function:

    1. Registers any ``joins`` as secondary tables in a :class:`LookupIndex`.
    2. Streams primary-table rows through
       :meth:`ObjectTransformer.map_object`.
    3. Drops secondary tables when the block is done.

    :param transformer: A configured :class:`ObjectTransformer`.
    :param data_loader: Loader that can resolve table names to file paths.
    :param source_type: Optional explicit source type override.
    :param on_error: Optional callback for row-level errors. When provided,
        :class:`TransformationError` is caught, enriched with row context,
        and passed to the callback. When ``None`` (default), errors propagate
        immediately (fail-fast).
    :param entity: Optional class name filter.  When provided, only
        top-level class_derivations whose ``name`` matches are processed.
    :returns: Iterator of transformed row dicts.
    """
    spec = transformer.derived_specification
    if spec is None:
        return

    if transformer.lookup_index is None:
        transformer.lookup_index = LookupIndex()

    for class_deriv in spec.class_derivations:
        if entity and class_deriv.name != entity:
            continue
        table_name = class_deriv.populated_from or class_deriv.name
        if table_name not in data_loader:
            logger.debug("Skipping class_derivation %s: no data found", class_deriv.name)
            continue

        joined_tables: list[str] = []
        try:
            # Register secondary (joined) tables
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
