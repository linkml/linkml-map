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
) -> Iterator[dict[str, Any]]:
    """
    Iterate class_derivation blocks and stream transformed rows.

    For each block whose ``populated_from`` names a loadable table, this
    function streams primary-table rows through
    :meth:`ObjectTransformer.map_object`. Joined (secondary) tables are
    registered **lazily** the first time a lookup needs them — and only the
    columns actually referenced are materialized — so a wide secondary table
    no longer loads in full. Registration uses ``data_loader.get_path``; a join
    that references a missing data file therefore fails fast at first use.

    At the end of each block, any sparse-join misses (source rows with no
    matching joined row) are summarized at INFO.

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
    # Resolve join table names to paths on demand, for lazy registration.
    transformer.lookup_index.path_resolver = data_loader.get_path

    try:
        for class_deriv in spec.class_derivations:
            table_name = class_deriv.populated_from or class_deriv.name
            if table_name not in data_loader:
                logger.debug("Skipping class_derivation %s: no data found", class_deriv.name)
                continue

            transformer.join_miss_counts.clear()
            row_count = 0
            for row_idx, row in enumerate(data_loader[table_name]):
                row_count = row_idx + 1
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

            for join_name, misses in sorted(transformer.join_miss_counts.items()):
                logger.info(
                    "join %r: %d of %d source rows had no matching row — nested object omitted",
                    join_name,
                    misses,
                    row_count,
                )
            transformer.join_miss_counts.clear()
    finally:
        if owns_index:
            # Close the index we created and detach it so a second call on the
            # same transformer reinitializes a fresh one rather than reusing
            # the now-closed connection.
            transformer.lookup_index.close()
            transformer.lookup_index = None
