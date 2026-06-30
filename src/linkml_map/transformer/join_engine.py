"""Set-based DuckDB join engine.

Replaces the per-row point-lookup join path with a single star ``LEFT JOIN`` per
primary block: all subject-keyed joined tables are gathered in one query, each as
a ``STRUCT`` column, and the existing :meth:`ObjectTransformer.map_object` runs
the per-field transforms over the enriched rows.

This consumes the normalizer's explicit joins (see
:meth:`Transformer._synthesize_implicit_joins`) — every cross-table reference is
already an explicit ``joins:`` entry, so the engine just reads them. ``map_object``
is unchanged: it receives a :class:`~linkml_map.transformer.object_transformer.MergedRow`
with each joined table's row inline, and ``_resolve_joined_row`` resolves from it
instead of a lookup. Nesting works to arbitrary depth because the merge carries
every joined table forward.

Scope: to-one equi-joins on a shared key (the real dbGaP corpus). One-to-many
*row aggregation* is not handled here — multivalued nesting comes from multiple
class_derivations, which this engine supports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import duckdb

from linkml_map.compiler.sql_compiler import LINKML_TO_SQL_TYPE_MAP
from linkml_map.loaders.data_loaders import FileFormat
from linkml_map.transformer.object_transformer import MergedRow
from linkml_map.utils.lookup_index import _duckdb_read_expr, _resolve_duckdb_settings

if TYPE_CHECKING:
    from collections.abc import Iterator

    from linkml_runtime import SchemaView

    from linkml_map.datamodel.transformer_model import AliasedClass, ClassDerivation
    from linkml_map.loaders.data_loaders import DataLoader
    from linkml_map.transformer.object_transformer import ObjectTransformer


def _collect_joins(class_deriv: ClassDerivation, acc: dict[str, AliasedClass]) -> dict[str, AliasedClass]:
    """Collect every join (this CD's and all nested CDs') keyed by joined table name."""
    for join in (class_deriv.joins or {}).values():
        acc.setdefault(join.alias, join)
    for slot_deriv in class_deriv.slot_derivations.values():
        for nested in slot_deriv.class_derivations or []:
            _collect_joins(nested, acc)
    return acc


def _cast(sv: SchemaView, cls: str, col: str, alias: str) -> str:
    """Return a column reference cast to its source-schema type (or left as text)."""
    rng = sv.induced_slot(col, cls).range
    sql_type = LINKML_TO_SQL_TYPE_MAP.get(rng, "TEXT")
    ref = f'{alias}."{col}"'
    return ref if sql_type == "TEXT" else f"CAST({ref} AS {sql_type})"


def _build_join_sql(
    primary: str,
    joins: dict[str, AliasedClass],
    sv: SchemaView,
    data_loader: DataLoader,
) -> tuple[str, list[str]]:
    """Build a star ``LEFT JOIN`` query and its path parameters (in FROM order).

    Each joined table becomes a ``STRUCT`` column named after the table; a miss
    (right key null) yields ``NULL`` so the nested object is suppressed (#217).
    """
    params: list[str] = []

    def reader(table: str, alias: str) -> str:
        path = str(data_loader.get_path(table))
        params.append(path)  # one '?' per reader, bound in FROM order
        return f"({_duckdb_read_expr(FileFormat.from_extension(path))}) {alias}"

    from_parts = [reader(primary, "m")]
    aliases: dict[str, tuple[str, str]] = {}  # table -> (alias, lookup_key)
    for i, (table, join) in enumerate(joins.items()):
        alias = f"j{i}"
        source_key = join.source_key or join.join_on
        lookup_key = join.lookup_key or join.join_on
        aliases[table] = (alias, lookup_key)
        from_parts.append(f'LEFT JOIN {reader(table, alias)} ON m."{source_key}" = {alias}."{lookup_key}"')

    def cols(cls: str) -> list[str]:
        return [s.name for s in sv.class_induced_slots(cls)]

    select = [f'{_cast(sv, primary, c, "m")} AS "{c}"' for c in cols(primary)]
    for table, (alias, lookup_key) in aliases.items():
        fields = ", ".join(f'"{c}" := {_cast(sv, table, c, alias)}' for c in cols(table))
        struct = f"STRUCT_PACK({fields})"
        select.append(f'CASE WHEN {alias}."{lookup_key}" IS NULL THEN NULL ELSE {struct} END AS "{table}"')

    sql = f"SELECT {', '.join(select)} FROM {' '.join(from_parts)}"  # noqa: S608 - identifiers from schema/spec
    return sql, params


def transform_via_join(
    transformer: ObjectTransformer,
    data_loader: DataLoader,
    source_type: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Stream transformed rows using one set-based join per class_derivation block.

    :param transformer: A configured :class:`ObjectTransformer` (its
        ``derived_specification`` supplies the explicit joins).
    :param data_loader: Loader resolving table names to file paths.
    :param source_type: Optional explicit source type override.
    :returns: Iterator of transformed row dicts.
    """
    spec = transformer.derived_specification
    if spec is None:
        return
    sv = transformer.source_schemaview

    con = duckdb.connect(":memory:")
    for name, value in _resolve_duckdb_settings().items():
        literal = value if isinstance(value, int) else "'" + str(value).replace("'", "''") + "'"
        con.execute(f"SET {name}={literal}")  # noqa: S608 - fixed names, sanitized values
    try:
        for class_deriv in spec.class_derivations:
            primary = class_deriv.populated_from or class_deriv.name
            if primary not in data_loader:
                continue
            joins = {t: j for t, j in _collect_joins(class_deriv, {}).items() if t in data_loader}
            sql, params = _build_join_sql(primary, joins, sv, data_loader)
            primary_cols = [s.name for s in sv.class_induced_slots(primary)]

            cursor = con.execute(sql, params)
            names = [d[0] for d in cursor.description]
            while batch := cursor.fetchmany(10000):
                for row in batch:
                    record = dict(zip(names, row))
                    primary_row = {c: record[c] for c in primary_cols}
                    rows_by_table = {primary: primary_row}
                    for table in joins:
                        rows_by_table[table] = record[table]  # STRUCT dict, or None on a miss
                    merged = MergedRow(primary_row, rows_by_table=rows_by_table)
                    yield transformer.map_object(
                        merged,
                        source_type=source_type or primary,
                        target_type=class_deriv.name,
                        class_derivation=class_deriv,
                    )
    finally:
        con.close()
