"""Tests for lazy registration and on-demand column accumulation in LookupIndex.

A joined table is registered with only its key column, then accumulates columns
as they are accessed — so a wide secondary table never loads in full. Referencing
a column that does not exist is a spec error and raises; a column that exists with
a null value returns None.
"""

from __future__ import annotations

import csv

import pytest

from linkml_map.utils.lookup_index import LookupIndex


@pytest.fixture()
def wide_csv(tmp_path):
    """A 'Reading' table with a key, one useful column, and many unused wide columns."""
    path = tmp_path / "Reading.csv"
    cols = ["subject_id", "score", *[f"extra{j}" for j in range(50)]]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i in range(20):
            w.writerow([f"S{i}", i, *[f"v{i}_{j}" for j in range(50)]])
    return path


def test_lazy_registration_loads_key_only(wide_csv):
    """ensure_registered materializes just the key column."""
    with LookupIndex() as idx:
        idx.path_resolver = lambda _name: wide_csv
        idx.ensure_registered("Reading", "subject_id")
        assert idx._tables["Reading"].materialized == {"subject_id"}


def test_ensure_registered_requires_path_resolver(wide_csv):
    """Lazy registration without a path resolver fails fast."""
    with LookupIndex() as idx:
        with pytest.raises(ValueError, match="path_resolver"):
            idx.ensure_registered("Reading", "subject_id")


def test_column_accumulates_on_demand(wide_csv):
    """ensure_column adds exactly the requested column and no others."""
    with LookupIndex() as idx:
        idx.path_resolver = lambda _name: wide_csv
        idx.ensure_registered("Reading", "subject_id")
        idx.ensure_column("Reading", "score")
        assert idx._tables["Reading"].materialized == {"subject_id", "score"}
        # Repeat access does not re-add or change the set.
        idx.ensure_column("Reading", "score")
        assert idx._tables["Reading"].materialized == {"subject_id", "score"}


def test_header_lists_all_columns_without_materializing(wide_csv):
    """header() exposes all column names while only the key stays materialized."""
    with LookupIndex() as idx:
        idx.path_resolver = lambda _name: wide_csv
        idx.ensure_registered("Reading", "subject_id")
        header = idx.header("Reading")
        assert "score" in header
        assert len([c for c in header if c.startswith("extra")]) == 50
        # header read does not pull columns into the table
        assert idx._tables["Reading"].materialized == {"subject_id"}


def test_lookup_returns_only_materialized_columns(wide_csv):
    """A lookup returns the key plus accumulated columns, not the whole wide row."""
    with LookupIndex() as idx:
        idx.path_resolver = lambda _name: wide_csv
        idx.ensure_registered("Reading", "subject_id")
        idx.ensure_column("Reading", "score")
        row = idx.lookup_row("Reading", "subject_id", "S3")
        assert row == {"subject_id": "S3", "score": 3}


def test_register_table_full_load_is_backward_compatible(wide_csv):
    """register_table without a columns list still loads every column (legacy callers)."""
    with LookupIndex() as idx:
        idx.register_table("Reading", wide_csv, "subject_id")
        row = idx.lookup_row("Reading", "subject_id", "S1")
        assert row["score"] == 1
        assert row["extra0"] == "v1_0"
        assert idx._tables["Reading"].full is True
