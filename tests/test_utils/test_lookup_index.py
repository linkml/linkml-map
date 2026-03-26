"""Tests for the DuckDB-backed LookupIndex."""

# ruff: noqa: ANN401

import pytest

from linkml_map.utils.lookup_index import LookupIndex


@pytest.fixture()
def tmp_tsv(tmp_path):
    """Create a simple TSV file and return its path."""
    tsv = tmp_path / "demo.tsv"
    tsv.write_text("id\tname\tage\nP001\tAlice\t30\nP002\tBob\t25\n")
    return tsv


@pytest.fixture()
def index():
    """Create a LookupIndex and close it after the test."""
    idx = LookupIndex()
    yield idx
    idx.close()


def test_register_and_lookup(index, tmp_tsv):
    """Register a table and look up a row by key."""
    index.register_table("demo", tmp_tsv, "id")
    row = index.lookup_row("demo", "id", "P001")
    assert row is not None
    assert row["name"] == "Alice"
    assert row["age"] == 30


def test_lookup_missing_row(index, tmp_tsv):
    """Looking up a nonexistent key returns None."""
    index.register_table("demo", tmp_tsv, "id")
    assert index.lookup_row("demo", "id", "MISSING") is None


def test_is_registered(index, tmp_tsv):
    """is_registered reflects table state."""
    assert not index.is_registered("demo")
    index.register_table("demo", tmp_tsv, "id")
    assert index.is_registered("demo")


def test_drop(index, tmp_tsv):
    """Dropping a table removes it from the index."""
    index.register_table("demo", tmp_tsv, "id")
    index.drop("demo")
    assert not index.is_registered("demo")


def test_drop_nonexistent(index):
    """Dropping a table that was never registered does not raise."""
    index.drop("nonexistent")


def test_csv_format(index, tmp_path):
    """CSV files are also handled by read_csv_auto."""
    csv = tmp_path / "data.csv"
    csv.write_text("id,value\nX1,100\nX2,200\n")
    index.register_table("data", csv, "id")
    row = index.lookup_row("data", "id", "X2")
    assert row is not None
    assert row["value"] == 200


def test_invalid_identifier(index):
    """SQL-injection-style identifiers are rejected."""
    with pytest.raises(ValueError, match="Invalid identifier"):
        index.register_table("drop table;--", "/dev/null", "id")


def test_numeric_coercion(index, tmp_path):
    """Numeric-looking values are coerced to int/float by lookup_row."""
    tsv = tmp_path / "nums.tsv"
    tsv.write_text("id\tcount\n1\t42\n2\t99\n")
    index.register_table("nums", tsv, "id")
    row = index.lookup_row("nums", "id", "1")
    assert row is not None
    assert row["count"] == 42
    assert isinstance(row["count"], int)
