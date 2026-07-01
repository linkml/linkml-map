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
key present in the primary. One-to-many *row aggregation* is not handled (the join
is deduped to one row per key to match the per-row ``LIMIT 1`` and avoid row
explosion); FK chains (``object_index``) and multi-hop dot paths fall back to the
per-row path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import duckdb

from linkml_map.loaders.data_loaders import FileFormat
from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import MergedRow
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


def can_use_join_engine(class_deriv: ClassDerivation, data_loader: DataLoader, sv: SchemaView | None) -> bool:
    """Whether a class_derivation block can be transformed by the set-based join engine.

    Conservative — returns ``False`` (fall back to the per-row path) unless every
    condition holds, so the engine is never used where it could diverge:

    - a source schema is available and the primary is one of its classes (needed
      to read the primary's columns; otherwise fall back rather than crash);
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
    if sv is None or primary not in sv.all_classes():
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

#: Prefix for the per-join STRUCT columns in the star query. Namespacing them keeps
#: a real primary column from colliding with a joined table/alias name (which would
#: otherwise drop that primary column from the row).
_JOIN_STRUCT_PREFIX = "__join__"


def _table_path(data_loader: DataLoader, table: str) -> str:
    """Resolve *table*'s file path (``get_path`` raises in single-file mode, so use ``base_path`` there)."""
    return str(data_loader.base_path if data_loader.is_single_file else data_loader.get_path(table))


def _duckdb_readable(data_loader: DataLoader, table: str) -> bool:
    """Whether *table*'s file can be read by the DuckDB join (CSV/TSV/JSON, not YAML)."""
    return FileFormat.from_extension(_table_path(data_loader, table)) in _DUCKDB_READABLE_FORMATS


def _readable_columns(con: duckdb.DuckDBPyConnection, path: str, fmt: FileFormat) -> set[str]:
    """Column names DuckDB actually exposes for the file at *path*.

    A 0-byte (headerless) file makes ``read_csv_auto`` return a single dummy
    ``column0`` rather than the schema's columns, so the join's ``lookup_key`` is
    absent. Probing here lets the caller degrade such a join to an all-miss null
    STRUCT instead of emitting SQL that binds a non-existent column (which raises
    ``BinderException`` and aborts the whole block, #276).
    """
    rows = con.execute(f"DESCRIBE {_duckdb_read_expr(fmt)}", [path]).fetchall()
    return {r[0] for r in rows}


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
    data_loader: DataLoader,
    con: duckdb.DuckDBPyConnection,
) -> tuple[str, list[str]]:
    """Build a star ``LEFT JOIN`` query and its path parameters (in FROM order).

    Columns are read as VARCHAR and coerced in Python with ``_parse_numeric`` (the
    same coercion the per-row lookup path uses), so typing matches exactly. Each
    joined table is deduped to one row per key (``QUALIFY``) to match the per-row
    ``LIMIT 1`` and avoid row explosion on a to-many table, becomes a ``STRUCT``
    column named after the table, and a miss yields ``NULL`` so the nested object
    is suppressed (#217).

    A joined file whose ``lookup_key`` column is absent (e.g. a 0-byte, headerless
    file — see :func:`_readable_columns`) is degraded to a literal ``NULL`` STRUCT,
    the same all-miss result a header-only file already produces, rather than
    joining on a non-existent column (#276).
    """
    params: list[str] = []

    def reader(table: str, alias: str, dedup_key: str | None = None) -> str:
        path = _table_path(data_loader, table)
        params.append(path)  # one '?' per reader, bound in FROM order
        select = _duckdb_read_expr(FileFormat.from_extension(path))
        if dedup_key is not None:
            select = f'{select} QUALIFY row_number() OVER (PARTITION BY "{dedup_key}") = 1'
        return f"({select}) {alias}"

    from_parts = [reader(primary, "m")]
    # m.* projects the primary's actual file columns; the bare alias jN projects
    # the whole joined row as a STRUCT (its real file columns, not schema slots —
    # which may include FK relationships that aren't data columns).
    struct_select = []
    for i, (table, join) in enumerate(joins.items()):
        alias = f"j{i}"
        source_key = join.source_key or join.join_on
        lookup_key = join.lookup_key or join.join_on
        path = _table_path(data_loader, table)
        if lookup_key not in _readable_columns(con, path, FileFormat.from_extension(path)):
            # Empty/headerless joined file: no key column to bind on. Emit an
            # all-miss null STRUCT so the nested object is suppressed (#217/#276).
            struct_select.append(f'NULL AS "{_JOIN_STRUCT_PREFIX}{table}"')
            continue
        from_parts.append(
            f'LEFT JOIN {reader(table, alias, dedup_key=lookup_key)} ON m."{source_key}" = {alias}."{lookup_key}"'
        )
        struct_select.append(
            f'CASE WHEN {alias}."{lookup_key}" IS NULL THEN NULL ELSE {alias} END AS "{_JOIN_STRUCT_PREFIX}{table}"'
        )

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
    # Every join is guaranteed loadable here (can_use_join_engine gates on it); a
    # missing table therefore fails loud in _build_join_sql rather than silently
    # dropping the join.
    joins = _collect_joins(class_deriv, {})
    sql, params = _build_join_sql(primary, joins, data_loader, con)

    cursor = con.execute(sql, params)
    names = [d[0] for d in cursor.description]
    # Join STRUCTs are namespaced (_JOIN_STRUCT_PREFIX); everything else is a real
    # primary column, so a primary column sharing a joined table's name is kept.
    primary_cols = [n for n in names if not n.startswith(_JOIN_STRUCT_PREFIX)]
    row_idx = 0
    while batch := cursor.fetchmany(10000):
        for row in batch:
            record = dict(zip(names, row))
            # Coerce VARCHAR values exactly as the per-row lookup path does.
            primary_row = {c: _parse_numeric(record[c]) for c in primary_cols}
            rows_by_table = {primary: primary_row}
            for table in joins:
                struct = record[f"{_JOIN_STRUCT_PREFIX}{table}"]  # STRUCT dict, or None on a miss
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
    """Transform every class_derivation block with the set-based join engine (all blocks).

    An explicit *force-engine* helper: it routes every block through the engine
    without a per-block capability check, so callers must ensure the spec is
    engine-capable (see :func:`can_use_join_engine`). Production dispatch lives in
    :func:`~linkml_map.transformer.engine.transform_spec`, which gates each block
    and falls back to the per-row path; this helper exists mainly for parity
    testing against that path.
    """
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
