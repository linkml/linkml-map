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


class LookupIndex:
    """
    In-memory DuckDB index for cross-table lookups.

    Each registered table is loaded from a CSV/TSV file via ``read_csv_auto``
    and indexed on a key column for fast single-row lookups.

    Delimiter detection uses :class:`~linkml_map.loaders.data_loaders.FileFormat`
    so that file parsing is consistent with :class:`~linkml_map.loaders.data_loaders.DataLoader`.
    """

    def __init__(self) -> None:
        """Initialize an empty lookup index with an in-memory DuckDB connection."""
        self._conn = duckdb.connect(":memory:")
        self._tables: dict[str, str] = {}  # table_name -> key_column

    def register_table(self, name: str, file_path: Path | str, key_column: str) -> None:
        """
        Load a CSV/TSV file into DuckDB and create an index on *key_column*.

        :param name: Logical table name (must be a valid identifier).
        :param file_path: Path to a CSV or TSV file.
        :param key_column: Column to index for lookups.
        """
        _validate_identifier(name)
        _validate_identifier(key_column)
        file_path = Path(file_path)
        fmt = FileFormat.from_extension(file_path)
        delim = {FileFormat.TSV: "\t", FileFormat.CSV: ","}[fmt]
        self._conn.execute(
            f"CREATE OR REPLACE TABLE {name} AS "  # noqa: S608
            "SELECT * FROM read_csv_auto(?, all_varchar=true, delim=?, null_padding=true)",
            [str(file_path), delim],
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
