"""Tests for container-aware DuckDB resource configuration on LookupIndex.

DuckDB sizes memory_limit/threads from the physical host and ignores cgroup
limits, which lets a memory-capped container be OOM-killed (an exit-less crash)
instead of failing with a catchable error. LookupIndex configures the connection
to respect the container; these tests verify that wiring.
"""

from __future__ import annotations

import os

import pytest

from linkml_map.utils.lookup_index import (
    _CGROUP_UNLIMITED,
    _ENV_MEMORY_LIMIT,
    _ENV_TEMP_DIR,
    _ENV_THREADS,
    LookupIndex,
    _detect_cgroup_memory_bytes,
    _resolve_duckdb_settings,
)


def _current_setting(index: LookupIndex, name: str) -> str:
    return index._conn.execute(f"SELECT current_setting('{name}')").fetchone()[0]


# --- cgroup detection ---


def test_detect_cgroup_v2_limit(tmp_path):
    """A numeric cgroup v2 memory.max is parsed to bytes."""
    f = tmp_path / "memory.max"
    f.write_text("4294967296\n")  # 4 GiB
    assert _detect_cgroup_memory_bytes((str(f),)) == 4294967296


def test_detect_cgroup_v2_unlimited(tmp_path):
    """A literal 'max' means no limit."""
    f = tmp_path / "memory.max"
    f.write_text("max\n")
    assert _detect_cgroup_memory_bytes((str(f),)) is None


def test_detect_cgroup_v1_unlimited_sentinel(tmp_path):
    """A near-max v1 sentinel is treated as unlimited, not a real limit."""
    f = tmp_path / "memory.limit_in_bytes"
    f.write_text(f"{_CGROUP_UNLIMITED + 4096}\n")
    assert _detect_cgroup_memory_bytes((str(f),)) is None


def test_detect_cgroup_missing_files_returns_none(tmp_path):
    """No readable cgroup file (e.g. local dev) yields None rather than raising."""
    assert _detect_cgroup_memory_bytes((str(tmp_path / "nope"),)) is None


def test_detect_cgroup_prefers_first_present(tmp_path):
    """The first readable path wins (v2 before v1)."""
    v2 = tmp_path / "memory.max"
    v2.write_text("2147483648")  # 2 GiB
    v1 = tmp_path / "memory.limit_in_bytes"
    v1.write_text("1073741824")  # 1 GiB
    assert _detect_cgroup_memory_bytes((str(v2), str(v1))) == 2147483648


# --- settings resolution ---


def test_env_memory_limit_overrides(monkeypatch):
    """An explicit env memory limit is honored verbatim."""
    monkeypatch.setenv(_ENV_MEMORY_LIMIT, "1500MiB")
    assert _resolve_duckdb_settings()["memory_limit"] == "1500MiB"


def test_env_threads_overrides(monkeypatch):
    """An explicit env thread count is honored and coerced to int."""
    monkeypatch.setenv(_ENV_THREADS, "3")
    assert _resolve_duckdb_settings()["threads"] == 3


def test_invalid_memory_limit_raises(monkeypatch):
    """A malformed memory limit fails fast rather than reaching DuckDB."""
    monkeypatch.setenv(_ENV_MEMORY_LIMIT, "lots of ram")
    with pytest.raises(ValueError, match="Invalid DuckDB memory limit"):
        _resolve_duckdb_settings()


@pytest.mark.parametrize("bad", ["lots", "0", "-2"])
def test_invalid_threads_raises(monkeypatch, bad):
    """A non-positive or non-integer thread count fails fast with a clear error."""
    monkeypatch.setenv(_ENV_THREADS, bad)
    with pytest.raises(ValueError, match="Invalid DuckDB thread count"):
        _resolve_duckdb_settings()


def test_threads_default_to_affinity(monkeypatch):
    """Without an override, threads default to the CPU affinity count (respects cpuset)."""
    monkeypatch.delenv(_ENV_THREADS, raising=False)
    expected = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count()
    assert _resolve_duckdb_settings()["threads"] == expected


def test_temp_directory_always_set(monkeypatch):
    """A concrete temp_directory is always provided so spilling has a target."""
    monkeypatch.delenv(_ENV_TEMP_DIR, raising=False)
    assert _resolve_duckdb_settings()["temp_directory"]


# --- end-to-end: settings actually land on the connection ---


def test_connection_applies_env_settings(monkeypatch):
    """Constructing a LookupIndex applies env-configured settings to the live connection."""
    monkeypatch.setenv(_ENV_MEMORY_LIMIT, "512MiB")
    monkeypatch.setenv(_ENV_THREADS, "2")
    with LookupIndex() as index:
        assert int(_current_setting(index, "threads")) == 2
        # DuckDB echoes memory_limit as a human string (e.g. "512.0 MiB"); assert it
        # reflects our 512MiB request rather than the multi-GiB host default.
        assert "512" in str(_current_setting(index, "memory_limit"))
