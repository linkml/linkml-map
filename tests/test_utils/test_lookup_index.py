"""Tests for the DuckDB-backed LookupIndex."""

# ruff: noqa: ANN401

import json

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


def test_json_format(index, tmp_path):
    """JSON files containing a flat array of objects can be registered and queried."""
    data = [
        {"id": "J1", "name": "Alice", "age": "30"},
        {"id": "J2", "name": "Bob", "age": "25"},
    ]
    jf = tmp_path / "data.json"
    jf.write_text(json.dumps(data))
    index.register_table("jdata", jf, "id")
    row = index.lookup_row("jdata", "id", "J2")
    assert row is not None
    assert row["name"] == "Bob"
    assert row["age"] == 25


def test_yaml_format_not_implemented(index, tmp_path):
    """YAML files raise NotImplementedError with a clear message."""
    yf = tmp_path / "data.yaml"
    yf.write_text("- id: Y1\n  name: Alice\n")
    with pytest.raises(NotImplementedError, match="yaml"):
        index.register_table("ydata", yf, "id")


def test_sparse_tsv_many_columns(index, tmp_path):
    """Sparse TSV with many columns and few populated fields loads correctly.

    Reproduces the bug from issue #209: DuckDB's read_csv_auto misdetects the
    delimiter when a TSV has many columns but sparse data rows, collapsing the
    entire header into a single column name.
    """
    cols = ["subject_id"] + [f"phv{i:08d}" for i in range(1, 201)]
    tsv = tmp_path / "sparse.tsv"
    header = "\t".join(cols)
    row = "SUBJ001\t65\tfoo"  # 3 values, 201 columns
    tsv.write_text(f"{header}\n{row}\n")

    index.register_table("sparse", tsv, "subject_id")
    result = index.lookup_row("sparse", "subject_id", "SUBJ001")
    assert result is not None
    assert result["subject_id"] == "SUBJ001"
    assert result["phv00000001"] == 65
    assert result["phv00000002"] == "foo"
    # Unpopulated columns should be None (null-padded)
    assert result["phv00000003"] is None
