"""``LookupIndex`` supports the context manager protocol.

The ``transform_spec`` resource-cleanup tests that used to live here exercise
``engine.py`` rather than ``LookupIndex``; they now sit in
``test_transformer/test_engine_index_lifecycle.py`` (issue #298).

See: https://github.com/linkml/linkml-map/issues/143
"""

import duckdb
import pytest

from linkml_map.utils.lookup_index import LookupIndex

# ---- Context manager protocol ----


def test_context_manager_basic(tmp_path):
    """LookupIndex should support the context manager protocol.

    After exiting the ``with`` block, both the internal table registry
    AND the underlying DuckDB connection should be cleaned up.
    """
    tsv = tmp_path / "data.tsv"
    tsv.write_text("id\tval\nA\t1\n")

    with LookupIndex() as idx:
        idx.register_table("data", tsv, "id")
        row = idx.lookup_row("data", "id", "A")
        assert row is not None
        assert str(row["val"]) == "1"

    # After exiting: table registry is cleared
    assert not idx.is_registered("data")

    # After exiting: DuckDB connection is actually closed — operations raise
    with pytest.raises((duckdb.ConnectionException, duckdb.InvalidInputException)):
        idx.register_table("data", tsv, "id")


def test_context_manager_cleans_up_on_exception(tmp_path):
    """LookupIndex context manager should close even if an exception occurs.

    Both the table registry and the DuckDB connection must be cleaned up
    regardless of how the ``with`` block exits.
    """
    tsv = tmp_path / "data.tsv"
    tsv.write_text("id\tval\nA\t1\n")

    with pytest.raises(RuntimeError):
        with LookupIndex() as idx:
            idx.register_table("data", tsv, "id")
            msg = "deliberate failure"
            raise RuntimeError(msg)

    # Table registry is cleared
    assert not idx.is_registered("data")

    # DuckDB connection is actually closed
    with pytest.raises((duckdb.ConnectionException, duckdb.InvalidInputException)):
        idx.register_table("data", tsv, "id")
