"""DuckDB-backed cross-table lookup index for join resolution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import duckdb

from linkml_map.loaders.data_loaders import FileFormat

_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_HAS_DIGIT_RE = re.compile(r"[0-9]")


def _parse_numeric(value: str) -> int | float | str:
    """Coerce a string to int or float if it looks numeric.

    Matches the behavior of ``linkml.validator.loaders``'s ``_parse_numeric``
    so that joined-table values are coerced the same way as primary-table values
    loaded via linkml's TsvLoader.
    """
    if not isinstance(value, str) or not _HAS_DIGIT_RE.search(value):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return value


def _validate_identifier(name: str) -> None:
    """Validate that *name* is a safe SQL identifier."""
    if not _IDENTIFIER_RE.match(name):
        msg = f"Invalid identifier: {name!r}"
        raise ValueError(msg)


def _duckdb_read_expr(fmt: FileFormat) -> str:
    """Return a DuckDB ``SELECT ... FROM read_*()`` expression for *fmt*.

    The returned SQL contains a single ``?`` placeholder for the file path.

    :raises NotImplementedError: For formats without DuckDB reader support.
    """
    if fmt == FileFormat.TSV:
        return "SELECT * FROM read_csv_auto(?, all_varchar=true, delim='\t', null_padding=true)"
    if fmt == FileFormat.CSV:
        return "SELECT * FROM read_csv_auto(?, all_varchar=true, delim=',', null_padding=true)"
    if fmt == FileFormat.JSON:
        return "SELECT CAST(columns(*) AS VARCHAR) FROM read_json_auto(?)"
    msg = f"LookupIndex does not yet support {fmt.value!r} files"
    raise NotImplementedError(msg)


class LookupIndex:
    """
    In-memory DuckDB index for cross-table lookups.

    Each registered table is loaded from a CSV, TSV, or JSON file and indexed
    on a key column for fast single-row lookups.

    Format detection uses :class:`~linkml_map.loaders.data_loaders.FileFormat`
    so that file parsing is consistent with :class:`~linkml_map.loaders.data_loaders.DataLoader`.
    """

    def __init__(self) -> None:
        """Initialize an empty lookup index with an in-memory DuckDB connection."""
        self._conn = duckdb.connect(":memory:")
        self._tables: dict[str, str] = {}  # table_name -> key_column

    def register_table(self, name: str, file_path: Path | str, key_column: str) -> None:
        """
        Load a data file into DuckDB and create an index on *key_column*.

        Supported formats: CSV, TSV, JSON (auto-detected from file extension
        via :class:`~linkml_map.loaders.data_loaders.FileFormat`).

        :param name: Logical table name (must be a valid identifier).
        :param file_path: Path to a data file.
        :param key_column: Column to index for lookups.
        :raises NotImplementedError: If the file format is not yet supported (e.g. YAML).
        """
        _validate_identifier(name)
        _validate_identifier(key_column)
        file_path = Path(file_path)
        fmt = FileFormat.from_extension(file_path)
        self._conn.execute(
            f"CREATE OR REPLACE TABLE {name} AS {_duckdb_read_expr(fmt)}",  # noqa: S608
            [str(file_path)],
        )
        self._conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{name}_{key_column} ON {name} ({key_column})"  # noqa: S608
        )
        self._tables[name] = key_column

    def lookup_row(
        self,
        table: str,
        key_col: str,
        key_val: Any,  # noqa: ANN401
    ) -> dict[str, Any] | None:
        """
        Return the first row matching *key_val* on *key_col*, or ``None``.

        :param table: Previously registered table name.
        :param key_col: Column to match on.
        :param key_val: Value to look up.
        :returns: Row as a dict, or None if not found.
        """
        _validate_identifier(table)
        _validate_identifier(key_col)
        result = self._conn.execute(
            f"SELECT * FROM {table} WHERE {key_col} = $1 LIMIT 1",  # noqa: S608
            [str(key_val)],
        ).fetchone()
        if result is None:
            return None
        columns = [desc[0] for desc in self._conn.description]
        return {col: _parse_numeric(val) for col, val in zip(columns, result)}

    def drop(self, table: str) -> None:
        """Drop a registered table, releasing memory."""
        _validate_identifier(table)
        self._conn.execute(f"DROP TABLE IF EXISTS {table}")  # noqa: S608
        self._tables.pop(table, None)

    def is_registered(self, table: str) -> bool:
        """Check whether *table* has been registered."""
        return table in self._tables

    def close(self) -> None:
        """Close the DuckDB connection."""
        self._conn.close()
        self._tables.clear()
