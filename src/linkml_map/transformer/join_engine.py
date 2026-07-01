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

Scope (see :func:`can_use_join_engine`): file-loadable tables joined to-one on a
key present in the primary. One-to-many *row aggregation* is not handled: the plain
join streams and its row explosion is collapsed in Python to one output per primary
row (matching the per-row ``LIMIT 1``), so the large joined table is never
materialized to dedup it. FK chains (``object_index``) and multi-hop dot paths fall
back to the per-row path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import duckdb

from linkml_map.loaders.data_loaders import FileFormat
from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import MergedRow
from linkml_map.utils.expression_locations import (
    extract_braced_bare_names,
    extract_table_column_references,
    iter_expressions,
)
from linkml_map.utils.lookup_index import _duckdb_read_expr, _parse_numeric, _resolve_duckdb_settings

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

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


def _collect_referenced_columns(
    class_deriv: ClassDerivation,
    source: str,
    joins: dict[str, AliasedClass],
    acc: dict[str, set[str]],
) -> dict[str, set[str]]:
    """Collect, per joined table, the columns this derivation reads from it.

    Projection narrows each joined ``STRUCT`` to only these columns so DuckDB reads
    only them from the file (whole-row STRUCTs otherwise pull every column of a wide
    table). Columns come from the three places the normalizer's join synthesis
    already walks — reusing :func:`extract_table_column_references` and
    :func:`iter_expressions` so the source-of-truth for "where references live"
    isn't duplicated:

    - ``{alias.col}`` in any expression (``expr`` / mapping fields);
    - a bare ``{col}`` in an expression on a CD sourced from a joined table (it
      resolves against that table's row at runtime);
    - a dotted ``populated_from: alias.col`` on a slot;
    - the bare ``populated_from`` slots of a nested CD sourced from a joined table.

    Collection is deliberately over-broad for bare references (a name may be a typo
    or a primary column); the caller intersects with the table's real file columns,
    so a non-existent name is simply not projected. Each join's key is added
    separately in :func:`_build_join_sql` (always needed for the ``ON`` clause and
    miss-suppression, independent of references).

    :param class_deriv: the derivation to scan (recursed for nested CDs).
    :param source: this derivation's source table (``populated_from``).
    :param joins: the collected joins, keyed by joined table/alias — only these are
        projected; references to the primary or an in-scope source are ignored.
    :param acc: accumulator mapping joined table -> referenced column set.
    :returns: *acc*, mutated in place.
    """
    aliases = set(joins)

    def add(table: str, col: str) -> None:
        if table in joins:
            acc.setdefault(table, set()).add(col)

    for deriv in (class_deriv, *class_deriv.slot_derivations.values()):
        for expression in iter_expressions(deriv):
            for table, cols in extract_table_column_references(expression, aliases).items():
                for col in cols:
                    add(table, col)
            if source in joins:  # bare {col} resolves against this CD's (joined) source
                for name in extract_braced_bare_names(expression):
                    add(source, name)

    for slot_deriv in class_deriv.slot_derivations.values():
        pf = slot_deriv.populated_from
        if pf and "." in pf:
            head, _, tail = pf.partition(".")
            add(head, tail)
        elif pf and source in joins:
            add(source, pf)
        for nested in slot_deriv.class_derivations or []:
            _collect_referenced_columns(nested, nested.populated_from or source, joins, acc)
    return acc


def _refs_engine_safe(class_deriv: ClassDerivation, available: set[str]) -> bool:
    """True if every dotted ``populated_from`` resolves to an available table (no FK chain / multi-hop).

    A dotted ``populated_from`` ``X.col`` is engine-safe only when ``X`` is the
    primary or a joined table (so it resolves from the MergedRow) and the field
    is a single column (no ``a.b.c`` foreign-key traversal, which needs
    ``object_index``).
    """
    for slot_deriv in class_deriv.slot_derivations.values():
        pf = slot_deriv.populated_from
        if pf and "." in pf:
            head, _, tail = pf.partition(".")
            if head not in available or "." in tail:
                return False
        for nested in slot_deriv.class_derivations or []:
            if not _refs_engine_safe(nested, available):
                return False
    return True


def can_use_join_engine(class_deriv: ClassDerivation, data_loader: DataLoader, sv: SchemaView) -> bool:
    """Whether a class_derivation block can be transformed by the set-based join engine.

    Conservative — returns ``False`` (fall back to the per-row path) unless every
    condition holds, so the engine is never used where it could diverge:

    - the primary and all joined tables are file-loadable in a DuckDB-readable
      format (CSV/TSV/JSON — not YAML, which ``_duckdb_read_expr`` can't read);
    - the block has joins (otherwise the per-row path is already lookup-free);
    - every join keys on a column present in the primary (a subject-keyed star
      join, not a multi-hop chain);
    - no dotted ``populated_from`` references an FK chain or a non-available table.
    """
    primary = class_deriv.populated_from or class_deriv.name
    if primary not in data_loader or not _duckdb_readable(data_loader, primary):
        return False
    joins = _collect_joins(class_deriv, {})
    if not joins:
        return False
    primary_cols = {s.name for s in sv.class_induced_slots(primary)}
    for table, join in joins.items():
        if table not in data_loader or not _duckdb_readable(data_loader, table):
            return False
        source_key = join.source_key or join.join_on
        if not source_key or source_key not in primary_cols:
            return False
    available = {primary, *joins}
    return _refs_engine_safe(class_deriv, available)


#: File formats the DuckDB join can read (matches :func:`_duckdb_read_expr`).
_DUCKDB_READABLE_FORMATS = frozenset({FileFormat.TSV, FileFormat.CSV, FileFormat.JSON})


def _duckdb_readable(data_loader: DataLoader, table: str) -> bool:
    """Whether *table*'s file can be read by the DuckDB join (CSV/TSV/JSON, not YAML)."""
    # get_path raises in single-file mode; use the single file's path directly there.
    path = data_loader.base_path if data_loader.is_single_file else data_loader.get_path(table)
    return FileFormat.from_extension(path) in _DUCKDB_READABLE_FORMATS


def _reader_columns(con: duckdb.DuckDBPyConnection, data_loader: DataLoader, table: str) -> set[str]:
    """Return the actual column names of *table*'s file (a cheap ``DESCRIBE``, header only).

    Referenced-column collection is over-broad (bare ``{name}`` refs may not be real
    columns); intersecting with this keeps projection to columns that truly exist,
    so ``struct_pack`` never names a missing column (which would be a SQL error).
    """
    path = str(data_loader.get_path(table))
    select = _duckdb_read_expr(FileFormat.from_extension(path))
    return {row[0] for row in con.execute(f"DESCRIBE {select}", [path]).fetchall()}


def make_connection() -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection configured to respect container limits (P1)."""
    con = duckdb.connect(":memory:")
    for name, value in _resolve_duckdb_settings().items():
        literal = value if isinstance(value, int) else "'" + str(value).replace("'", "''") + "'"
        con.execute(f"SET {name}={literal}")  # noqa: S608 - fixed names, sanitized values
    return con


def _build_join_sql(
    primary: str,
    joins: dict[str, AliasedClass],
    referenced: dict[str, set[str]],
    data_loader: DataLoader,
) -> tuple[str, list[str]]:
    """Build a star ``LEFT JOIN`` query and its path parameters (in FROM order).

    Columns are read as VARCHAR and coerced in Python with ``_parse_numeric`` (the
    same coercion the per-row lookup path uses), so typing matches exactly. Each
    joined table becomes a ``STRUCT`` column named after the table, and a miss
    yields ``NULL`` so the nested object is suppressed (#217). The join is *plain*
    (no in-SQL dedup): a ``QUALIFY``/``DISTINCT ON`` window would materialize the
    whole joined table to dedup it, which is fatal for million-row tables. Instead
    the join streams and its to-many row explosion is collapsed to one row per
    primary in :func:`transform_block_via_join`, so only the small side is held.

    The STRUCT is projected to only the columns the derivation reads (*referenced*,
    from :func:`_collect_referenced_columns`) plus the join key. A whole-row STRUCT
    would pull every column of a wide table; naming the columns lets DuckDB push the
    projection down into the CSV/TSV scan and read only those (~2x less memory, much
    faster on wide ``pht`` tables).
    """
    params: list[str] = []

    def reader(table: str, alias: str) -> str:
        path = str(data_loader.get_path(table))
        params.append(path)  # one '?' per reader, bound in FROM order
        select = _duckdb_read_expr(FileFormat.from_extension(path))
        return f"({select}) {alias}"

    from_parts = [reader(primary, "m")]
    # m.* projects the primary's actual file columns; each joined table is packed
    # into a STRUCT of only its referenced columns (real file columns, not schema
    # slots — which may include FK relationships that aren't data columns).
    struct_select = []
    for i, (table, join) in enumerate(joins.items()):
        alias = f"j{i}"
        source_key = join.source_key or join.join_on
        lookup_key = join.lookup_key or join.join_on
        from_parts.append(f'LEFT JOIN {reader(table, alias)} ON m."{source_key}" = {alias}."{lookup_key}"')
        cols = sorted(referenced.get(table, set()) | {lookup_key})
        fields = ", ".join(f'"{c}" := {alias}."{c}"' for c in cols)
        struct = f"struct_pack({fields})"
        struct_select.append(f'CASE WHEN {alias}."{lookup_key}" IS NULL THEN NULL ELSE {struct} END AS "{table}"')

    projection = "m.*" + ("".join(f", {s}" for s in struct_select))
    sql = f"SELECT {projection} FROM {' '.join(from_parts)}"  # noqa: S608 - identifiers from schema/spec
    return sql, params


def transform_block_via_join(
    transformer: ObjectTransformer,
    data_loader: DataLoader,
    class_deriv: ClassDerivation,
    source_type: str | None,
    con: duckdb.DuckDBPyConnection,
    on_error: Callable[[TransformationError], None] | None = None,
) -> Iterator[dict[str, Any]]:
    """Transform one class_derivation block with a single set-based join query."""
    primary = class_deriv.populated_from or class_deriv.name
    joins = {t: j for t, j in _collect_joins(class_deriv, {}).items() if t in data_loader}
    referenced = _collect_referenced_columns(class_deriv, primary, joins, {})
    # Keep only columns that truly exist in each file — over-broad bare-ref names
    # are dropped rather than becoming a struct_pack SQL error.
    projected = {t: referenced.get(t, set()) & _reader_columns(con, data_loader, t) for t in joins}
    sql, params = _build_join_sql(primary, joins, projected, data_loader)

    sv = transformer.source_schemaview
    primary_id = next((s.name for s in sv.class_induced_slots(primary) if s.identifier), None)

    cursor = con.execute(sql, params)
    names = [d[0] for d in cursor.description]
    primary_cols = [n for n in names if n not in joins]  # everything that isn't a join struct
    # A plain to-many join emits one row per (primary, joined-match) pair; collapse
    # back to one output per primary row to match the per-row path's LIMIT 1. Keyed
    # on the primary identifier when present, else the whole primary row. The set is
    # bounded by the primary row count (ids only), so the joined table still streams.
    seen: set[Any] = set()
    row_idx = 0
    while batch := cursor.fetchmany(10000):
        for row in batch:
            record = dict(zip(names, row))
            # Coerce VARCHAR values exactly as the per-row lookup path does.
            primary_row = {c: _parse_numeric(record[c]) for c in primary_cols}
            collapse_key = primary_row[primary_id] if primary_id in primary_row else tuple(primary_row.values())
            if collapse_key in seen:
                continue
            seen.add(collapse_key)
            rows_by_table = {primary: primary_row}
            for table in joins:
                struct = record[table]  # STRUCT dict, or None on a miss
                rows_by_table[table] = {k: _parse_numeric(v) for k, v in struct.items()} if struct else struct
            merged = MergedRow(primary_row, rows_by_table=rows_by_table)
            try:
                yield transformer.map_object(
                    merged,
                    source_type=source_type or primary,
                    target_type=class_deriv.name,
                    class_derivation=class_deriv,
                )
            except TransformationError as err:
                if on_error is None:
                    raise
                err.row_index = row_idx
                err.class_derivation_name = err.class_derivation_name or class_deriv.name
                on_error(err)
            row_idx += 1


def transform_via_join(
    transformer: ObjectTransformer,
    data_loader: DataLoader,
    source_type: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Transform every class_derivation block with the set-based join engine (all blocks)."""
    spec = transformer.derived_specification
    if spec is None:
        return
    con = make_connection()
    try:
        for class_deriv in spec.class_derivations:
            primary = class_deriv.populated_from or class_deriv.name
            if primary not in data_loader:
                continue
            yield from transform_block_via_join(transformer, data_loader, class_deriv, source_type, con)
    finally:
        con.close()
