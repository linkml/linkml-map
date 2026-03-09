"""Tests for LookupIndex context manager protocol and resource cleanup.

These tests verify that LookupIndex supports ``with`` statement usage
and that transform_spec properly cleans up its LookupIndex. Currently,
LookupIndex does NOT implement __enter__/__exit__, so these tests are
expected to fail until the protocol is added.

See: https://github.com/linkml/linkml-map/issues/143
"""

import textwrap

import duckdb
import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.utils.lookup_index import LookupIndex


# ---- Context manager protocol ----


def test_context_manager_basic(tmp_path):
    """LookupIndex should support the context manager protocol."""
    tsv = tmp_path / "data.tsv"
    tsv.write_text("id\tval\nA\t1\n")

    with LookupIndex() as idx:
        idx.register_table("data", tsv, "id")
        row = idx.lookup_row("data", "id", "A")
        assert row is not None
        assert row["val"] == "1"

    # After exiting the context, the connection should be closed
    assert not idx.is_registered("data")


def test_context_manager_cleans_up_on_exception(tmp_path):
    """LookupIndex context manager should close even if an exception occurs."""
    tsv = tmp_path / "data.tsv"
    tsv.write_text("id\tval\nA\t1\n")

    with pytest.raises(RuntimeError):
        with LookupIndex() as idx:
            idx.register_table("data", tsv, "id")
            msg = "deliberate failure"
            raise RuntimeError(msg)

    # Connection should still be cleaned up
    assert not idx.is_registered("data")


# ---- transform_spec resource cleanup ----


SOURCE_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/cleanup-test-source
    name: cleanup_test_source
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string
    classes:
      samples:
        attributes:
          sample_id:
            identifier: true
          name: {}
          site_code: {}
      sites:
        attributes:
          site_code:
            identifier: true
          site_name: {}
""")

TARGET_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/cleanup-test-target
    name: cleanup_test_target
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string
    classes:
      FlatSample:
        attributes:
          sample_id:
            identifier: true
          name: {}
          site_name: {}
""")


def test_transform_spec_closes_lookup_index(tmp_path):
    """transform_spec should close its LookupIndex after iteration completes.

    Currently, transform_spec creates a LookupIndex but never calls close(),
    leaking the DuckDB connection. This test verifies proper cleanup.
    """
    (tmp_path / "samples.tsv").write_text(
        "sample_id\tname\tsite_code\n"
        "S001\tAlpha\tSITE_A\n"
    )
    (tmp_path / "sites.tsv").write_text(
        "site_code\tsite_name\n"
        "SITE_A\tBoston Medical\n"
    )

    spec_yaml = textwrap.dedent("""\
        class_derivations:
          FlatSample:
            populated_from: samples
            joins:
              sites:
                join_on: site_code
            slot_derivations:
              sample_id:
                populated_from: sample_id
              site_name:
                expr: "{sites.site_name}"
    """)

    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(TARGET_SCHEMA_YAML)
    tr = ObjectTransformer(unrestricted_eval=False)
    tr.source_schemaview = source_sv
    tr.target_schemaview = target_sv
    tr.create_transformer_specification(yaml.safe_load(spec_yaml))

    loader = DataLoader(tmp_path)

    # Consume the iterator fully
    results = list(transform_spec(tr, loader))
    assert len(results) == 1

    # After transform_spec completes, the LookupIndex should be closed.
    # Attempting to use it should fail.
    with pytest.raises((duckdb.ConnectionException, duckdb.InvalidInputException)):
        tr.lookup_index.register_table(
            "should_fail", tmp_path / "sites.tsv", "site_code"
        )
