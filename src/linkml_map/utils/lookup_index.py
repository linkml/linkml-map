"""DuckDB-backed cross-table lookup index for join resolution."""

from __future__ import annotations

import logging
import os
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from linkml_map.loaders.data_loaders import FileFormat

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_HAS_DIGIT_RE = re.compile(r"[0-9]")

# DuckDB sizes its memory_limit (~80% of RAM) and thread pool from the *physical
# host*, ignoring container cgroup limits. In a memory-capped container that lets
# it allocate past the cap, so the kernel OOM-killer SIGKILLs the process (an
# exit-less crash, no traceback) or it thrashes into a apparent hang. We detect
# the cgroup limit and configure DuckDB to respect it, turning a silent OOM-kill
# into a catchable OutOfMemoryException. See join-performance investigation.
_MEMORY_FRACTION = 0.8  # leave headroom for the Python process / OS
_CGROUP_V2_MEMORY = "/sys/fs/cgroup/memory.max"
_CGROUP_V1_MEMORY = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
_CGROUP_UNLIMITED = 1 << 62  # cgroup v1 "unlimited" sentinel is a near-max int
_MEMORY_LIMIT_RE = re.compile(r"^\d+(\.\d+)?\s*([KMGT]i?B|%)?$", re.IGNORECASE)

_ENV_MEMORY_LIMIT = "LINKML_MAP_DUCKDB_MEMORY_LIMIT"
_ENV_THREADS = "LINKML_MAP_DUCKDB_THREADS"
_ENV_TEMP_DIR = "LINKML_MAP_DUCKDB_TEMP_DIR"


def _detect_cgroup_memory_bytes(paths: tuple[str, ...] = (_CGROUP_V2_MEMORY, _CGROUP_V1_MEMORY)) -> int | None:
    """Return the container memory limit in bytes, or ``None`` if unlimited/undetectable.

    Reads the cgroup v2 (``memory.max``) then v1 (``memory.limit_in_bytes``)
    interfaces. A literal ``max`` (v2) or near-max sentinel (v1) means no limit.

    :param paths: cgroup interface files to try, in order. Parameterized for testing.
    """
    for path in paths:
        try:
            raw = Path(path).read_text().strip()
        except OSError:
            continue
        if raw == "max":
            return None
        value = int(raw)
        if value >= _CGROUP_UNLIMITED:
            return None
        return value
    return None


def _resolve_duckdb_settings() -> dict[str, str | int]:
    """Resolve DuckDB connection settings honoring the container and env overrides.

    Precedence for each setting: explicit ``LINKML_MAP_DUCKDB_*`` env var, then a
    value derived from the cgroup limit, then DuckDB's own default (omitted here).

    - ``memory_limit``: ``_MEMORY_FRACTION`` of the detected cgroup limit, leaving
      headroom for the rest of the process. Omitted when no limit is detected.
    - ``threads``: the CPU affinity count (respects cpuset), so we don't spin a
      host-sized thread pool on a few container vCPUs.
    - ``temp_directory``: a concrete writable path so spillable operators have
      somewhere to go (DuckDB's default can be a relative path).

    :returns: Mapping of DuckDB setting name to value, ready to ``SET``.
    """
    settings: dict[str, str | int] = {}

    memory_limit = os.environ.get(_ENV_MEMORY_LIMIT)
    if not memory_limit:
        cgroup_bytes = _detect_cgroup_memory_bytes()
        if cgroup_bytes:
            budget_mib = int(cgroup_bytes * _MEMORY_FRACTION) // (1024 * 1024)
            memory_limit = f"{budget_mib}MiB"
    if memory_limit:
        if not _MEMORY_LIMIT_RE.match(memory_limit.strip()):
            msg = f"Invalid DuckDB memory limit {memory_limit!r} (expected e.g. '2GB', '512MiB', '80%')"
            raise ValueError(msg)
        settings["memory_limit"] = memory_limit.strip()

    threads = os.environ.get(_ENV_THREADS)
    if threads:
        settings["threads"] = int(threads)
    elif hasattr(os, "sched_getaffinity"):
        settings["threads"] = len(os.sched_getaffinity(0))
    elif os.cpu_count():
        settings["threads"] = os.cpu_count()

    settings["temp_directory"] = os.environ.get(_ENV_TEMP_DIR) or tempfile.gettempdir()

    return settings


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


def _reader_source(fmt: FileFormat) -> str:
    """Return the DuckDB ``read_*(...)`` table-function for *fmt* (one ``?`` for the path).

    :raises NotImplementedError: For formats without DuckDB reader support.
    """
    if fmt == FileFormat.TSV:
        return "read_csv_auto(?, all_varchar=true, delim='\t', null_padding=true)"
    if fmt == FileFormat.CSV:
        return "read_csv_auto(?, all_varchar=true, delim=',', null_padding=true)"
    if fmt == FileFormat.JSON:
        return "read_json_auto(?)"
    msg = f"LookupIndex does not yet support {fmt.value!r} files"
    raise NotImplementedError(msg)


def _projected_select(fmt: FileFormat, columns: list[str] | None) -> str:
    """Return a ``SELECT ... FROM read_*()`` statement, projected to *columns*.

    When *columns* is ``None`` all columns are selected (``SELECT *``). JSON
    values are cast to VARCHAR (matching the unprojected reader) so that joined
    values coerce consistently with primary-table values.

    :param fmt: File format.
    :param columns: Columns to project, or ``None`` for all columns.
    """
    source = _reader_source(fmt)
    if columns is None:
        all_cols = "CAST(columns(*) AS VARCHAR)" if fmt == FileFormat.JSON else "*"
        return f"SELECT {all_cols} FROM {source}"
    if fmt == FileFormat.JSON:
        projection = ", ".join(f"CAST({c} AS VARCHAR) AS {c}" for c in columns)
    else:
        projection = ", ".join(columns)
    return f"SELECT {projection} FROM {source}"


@dataclass
class _TableState:
    """Bookkeeping for one registered table.

    :ivar path: Source file path (string form, for DuckDB parameter binding).
    :ivar fmt: File format, used to rebuild the reader on column accumulation.
    :ivar key: Indexed key column.
    :ivar materialized: Columns currently loaded into the DuckDB table.
    :ivar full: ``True`` when the table was loaded with all columns (no projection);
        column accumulation is then a no-op.
    :ivar header: All column names in the source file, lazily read once via ``DESCRIBE``.
    """

    path: str
    fmt: FileFormat
    key: str
    materialized: set[str]
    full: bool
    header: list[str] | None = None


class LookupIndex:
    """
    In-memory DuckDB index for cross-table lookups.

    Each registered table is loaded from a CSV, TSV, or JSON file and indexed
    on a key column for fast single-row lookups.

    Format detection uses :class:`~linkml_map.loaders.data_loaders.FileFormat`
    so that file parsing is consistent with :class:`~linkml_map.loaders.data_loaders.DataLoader`.
    """

    def __init__(self) -> None:
        """Initialize an empty lookup index with an in-memory DuckDB connection.

        The connection is configured to respect container cgroup limits (memory
        and CPU) rather than DuckDB's host-derived defaults, so a memory-capped
        container fails with a catchable error instead of being OOM-killed.
        """
        self._conn = duckdb.connect(":memory:")
        self._configure_connection()
        self._tables: dict[str, _TableState] = {}
        #: Resolves a table name to its data file path. Set by the caller (engine)
        #: to enable lazy registration on first lookup.
        self.path_resolver: Callable[[str], Path] | None = None

    def _configure_connection(self) -> None:
        """Apply container-aware ``memory_limit``/``threads``/``temp_directory`` settings."""
        for name, value in _resolve_duckdb_settings().items():
            literal = value if isinstance(value, int) else "'" + str(value).replace("'", "''") + "'"
            self._conn.execute(f"SET {name}={literal}")  # noqa: S608 - name is a fixed literal, value sanitized
        logger.debug("Configured DuckDB connection: %s", _resolve_duckdb_settings())

    def register_table(
        self,
        name: str,
        file_path: Path | str,
        key_column: str,
        columns: list[str] | None = None,
    ) -> None:
        """
        Load a data file into DuckDB and create an index on *key_column*.

        Supported formats: CSV, TSV, JSON (auto-detected from file extension
        via :class:`~linkml_map.loaders.data_loaders.FileFormat`).

        :param name: Logical table name (must be a valid identifier).
        :param file_path: Path to a data file.
        :param key_column: Column to index for lookups.
        :param columns: Columns to load (the key is always included). ``None`` loads
            all columns; an explicit list (possibly empty) enables lazy accumulation
            via :meth:`ensure_column`.
        :raises NotImplementedError: If the file format is not yet supported (e.g. YAML).
        """
        _validate_identifier(name)
        _validate_identifier(key_column)
        file_path = Path(file_path)
        fmt = FileFormat.from_extension(file_path)
        if columns is None:
            materialized, full = {key_column}, True
        else:
            materialized = {key_column, *columns}
            for col in materialized:
                _validate_identifier(col)
            full = False
        self._tables[name] = _TableState(str(file_path), fmt, key_column, materialized, full)
        self._build(name)

    def _build(self, name: str) -> None:
        """(Re)create the DuckDB table for *name* from its current materialized columns."""
        st = self._tables[name]
        select = _projected_select(st.fmt, None if st.full else sorted(st.materialized))
        self._conn.execute(f"CREATE OR REPLACE TABLE {name} AS {select}", [st.path])  # noqa: S608
        self._conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{name}_{st.key} ON {name} ({st.key})"  # noqa: S608
        )

    def ensure_registered(self, name: str, key_column: str) -> None:
        """Lazily register *name* (key column only) on first use.

        The file path is resolved via :attr:`path_resolver`; a missing file
        therefore fails fast here rather than silently producing no matches.

        :raises ValueError: If :attr:`path_resolver` has not been set.
        """
        if name in self._tables:
            return
        if self.path_resolver is None:
            msg = "LookupIndex.path_resolver must be set before lazy registration"
            raise ValueError(msg)
        self.register_table(name, self.path_resolver(name), key_column, columns=[])

    def ensure_column(self, name: str, column: str) -> None:
        """Ensure *column* is materialized for *name*, rebuilding the table if needed.

        No-op for tables loaded in full (unprojected) mode or columns already present.
        """
        st = self._tables[name]
        if st.full or column in st.materialized:
            return
        _validate_identifier(column)
        st.materialized.add(column)
        self._build(name)

    def header(self, name: str) -> list[str]:
        """Return all column names in *name*'s source file, without loading data."""
        st = self._tables[name]
        if st.header is None:
            select = _projected_select(st.fmt, None)
            rows = self._conn.execute(f"DESCRIBE {select}", [st.path]).fetchall()  # noqa: S608
            st.header = [r[0] for r in rows]
        return st.header

    def lookup_row(
        self,
        table: str,
        key_col: str,
        key_val: Any,  # noqa: ANN401
    ) -> dict[str, Any] | None:
        """
        Return the first row matching *key_val* on *key_col*, or ``None`` if no row matches.

        Only currently-materialized columns are returned; absent columns are
        loaded on demand by :class:`LazyJoinRow` via :meth:`ensure_column`.

        :param table: Previously registered table name.
        :param key_col: Column to match on.
        :param key_val: Value to look up.
        :returns: Row as a dict, or None if no row matches the key.
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

    def __enter__(self) -> LookupIndex:
        """Enter the context manager."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Exit the context manager, closing the DuckDB connection."""
        self.close()

    def close(self) -> None:
        """Close the DuckDB connection."""
        self._conn.close()
        self._tables.clear()
