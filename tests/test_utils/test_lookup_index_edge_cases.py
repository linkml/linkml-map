"""Edge-case tests for LookupIndex (supplements test_lookup_index.py).

Covers:
- Duplicate key behavior (LIMIT 1 first-match semantics)
- Empty tables (headers only, zero data rows)
- Lifecycle after close() (operations should fail gracefully)

See: https://github.com/linkml/linkml-map/pull/136
"""

import duckdb
import pytest

from linkml_map.utils.lookup_index import LookupIndex


@pytest.fixture()
def index():
    """Create a LookupIndex and close it after the test."""
    idx = LookupIndex()
    yield idx
    idx.close()


# ---- Duplicate key behavior ----


def test_duplicate_keys_returns_a_row(index, tmp_path):
    """When multiple rows share the same key, lookup_row returns one of them.

    The current implementation uses ``LIMIT 1`` without an ``ORDER BY``,
    so the returned row is deterministic per DuckDB's storage order (insertion
    order for ``read_csv_auto``) but this is NOT guaranteed by the API.
    This test documents the behavior without asserting which duplicate wins.
    """
    tsv = tmp_path / "dupes.tsv"
    tsv.write_text(
        "participant_id\tname\tage\n"
        "P001\tAlice\t30\n"
        "P001\tAlice-v2\t31\n"
        "P002\tBob\t25\n"
    )
    index.register_table("dupes", tsv, "participant_id")
    row = index.lookup_row("dupes", "participant_id", "P001")

    # A row IS returned (not None)
    assert row is not None
    assert row["participant_id"] == "P001"
    # The name is one of the two duplicate rows
    assert row["name"] in {"Alice", "Alice-v2"}


def test_duplicate_keys_unique_rows_unaffected(index, tmp_path):
    """Rows with unique keys are unaffected by the presence of duplicates elsewhere."""
    tsv = tmp_path / "dupes.tsv"
    tsv.write_text(
        "id\tvalue\n"
        "A\t1\n"
        "A\t2\n"
        "B\t3\n"
    )
    index.register_table("dupes", tsv, "id")
    row = index.lookup_row("dupes", "id", "B")
    assert row is not None
    assert row["value"] == "3"


# ---- Empty tables ----


def test_empty_table_headers_only(index, tmp_path):
    """A table with column headers but zero data rows can be registered and queried."""
    tsv = tmp_path / "empty.tsv"
    tsv.write_text("id\tname\tage\n")
    index.register_table("empty", tsv, "id")

    assert index.is_registered("empty")
    assert index.lookup_row("empty", "id", "anything") is None


def test_empty_table_then_drop(index, tmp_path):
    """An empty table can be dropped without error."""
    tsv = tmp_path / "empty.tsv"
    tsv.write_text("id\tvalue\n")
    index.register_table("empty", tsv, "id")
    index.drop("empty")
    assert not index.is_registered("empty")


# ---- Lifecycle after close() ----


def test_close_clears_tables(index, tmp_path):
    """After close(), is_registered returns False for all tables."""
    tsv = tmp_path / "data.tsv"
    tsv.write_text("id\tval\nA\t1\n")
    index.register_table("data", tsv, "id")
    assert index.is_registered("data")

    index.close()
    assert not index.is_registered("data")


def test_operations_after_close_raise(tmp_path):
    """Register and lookup operations after close() raise an error."""
    idx = LookupIndex()
    idx.close()

    tsv = tmp_path / "data.tsv"
    tsv.write_text("id\tval\nA\t1\n")

    with pytest.raises((duckdb.ConnectionException, duckdb.InvalidInputException)):
        idx.register_table("data", tsv, "id")


def test_double_close_is_safe():
    """Calling close() twice does not raise."""
    idx = LookupIndex()
    idx.close()
    # Second close should not raise
    idx.close()
