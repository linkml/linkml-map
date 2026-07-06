"""Tests for LookupIndex context manager protocol and resource cleanup.

Verifies that LookupIndex supports ``with`` statement usage and that
``transform_spec`` properly closes (and detaches) the LookupIndex it
created after iteration completes.

See: https://github.com/linkml/linkml-map/issues/143
"""

import textwrap

import duckdb
import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer
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


# ---- transform_spec resource cleanup ----
#
# These exercise the LookupIndex the *per-row fallback* owns and cleans up. The
# primary table is written as YAML (``samples.yaml``): YAML isn't DuckDB-readable,
# so ``can_use_join_engine`` returns False and the block takes the per-row path,
# which creates and owns the index. The TSV join table stays LookupIndex-compatible.
# (With a TSV primary the block is engine-capable and no fallback index is created,
# so these lifecycle assertions wouldn't exercise anything.)


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
    """transform_spec must clean up the LookupIndex it owns after iteration.

    When transform_spec creates its own LookupIndex (the caller did not
    pre-attach one), it closes the connection AND detaches it from the
    transformer in the outer ``finally``. Detaching is required so a
    second call on the same transformer reinitializes a fresh index
    rather than reusing the now-closed connection.

    Both signals are required for the test to pass:
    - ``transformer.lookup_index is None`` (detached), AND
    - operations on the held index instance raise (closed).
    Asserting only one would let a regression that does the other slip
    through.
    """
    (tmp_path / "samples.yaml").write_text("- sample_id: S001\n  name: Alpha\n  site_code: SITE_A\n")
    (tmp_path / "sites.tsv").write_text("site_code\tsite_name\nSITE_A\tBoston Medical\n")

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

    # Capture the LookupIndex during iteration — before the cleanup finally runs.
    held_index: LookupIndex | None = None
    results = []
    for row in transform_spec(tr, loader):
        if held_index is None:
            held_index = tr.lookup_index
        results.append(row)
    assert len(results) == 1

    # Both signals must hold: detached AND closed. Asserting only one would
    # let a regression that does the other slip through.
    assert held_index is not None, "did not capture index during iteration"
    assert tr.lookup_index is None, "owned index should be detached after iteration"
    with pytest.raises((duckdb.ConnectionException, duckdb.InvalidInputException)):
        held_index.register_table("should_fail", tmp_path / "sites.tsv", "site_code")


def test_transform_spec_can_be_called_twice_on_same_transformer(tmp_path):
    """A second transform_spec call on the same transformer must succeed.

    When transform_spec owns the LookupIndex it creates, it must detach the
    closed index in the cleanup ``finally`` so a subsequent call does not
    skip reinitialization (``owns_index`` would be False) and try to register
    join tables on a closed connection.
    """
    (tmp_path / "samples.yaml").write_text("- sample_id: S001\n  name: Alpha\n  site_code: SITE_A\n")
    (tmp_path / "sites.tsv").write_text("site_code\tsite_name\nSITE_A\tBoston Medical\n")

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

    # First call — should succeed and clean up
    first = list(transform_spec(tr, loader))
    assert len(first) == 1

    # Second call on the same transformer — must succeed, not blow up on a
    # closed connection from the first call.
    second = list(transform_spec(tr, loader))
    assert len(second) == 1
    assert second[0]["site_name"] == first[0]["site_name"]


def test_transform_spec_does_not_close_caller_supplied_index(tmp_path):
    """A caller-supplied LookupIndex must be left intact after transform_spec.

    Ownership is the contract: when the caller pre-attaches an index,
    transform_spec must not close or detach it — the caller is responsible
    for its lifecycle.
    """
    (tmp_path / "samples.yaml").write_text("- sample_id: S001\n  name: Alpha\n  site_code: SITE_A\n")
    (tmp_path / "sites.tsv").write_text("site_code\tsite_name\nSITE_A\tBoston Medical\n")

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

    caller_index = LookupIndex()
    tr.lookup_index = caller_index

    loader = DataLoader(tmp_path)
    results = list(transform_spec(tr, loader))
    assert len(results) == 1

    # Caller's index must still be attached and still usable.
    assert tr.lookup_index is caller_index, "caller-supplied index must not be detached"
    extra_tsv = tmp_path / "extra.tsv"
    extra_tsv.write_text("k\tv\nA\t1\n")
    caller_index.register_table("extra", extra_tsv, "k")
    assert caller_index.is_registered("extra")
    caller_index.close()  # caller's responsibility


def test_transform_spec_closes_owned_index_on_exception(tmp_path):
    """When iteration raises, the owned index must still be closed and detached.

    The leak fix relies on the outer ``try/finally`` running cleanup even when
    iteration exits exceptionally. A regression that moves the close out of the
    finally would silently break this without dedicated coverage.
    """
    # Two rows: first succeeds, second triggers an IndexError via string
    # indexing past the end of the name. The first successful yield gives the
    # test a chance to capture tr.lookup_index before the cleanup finally runs.
    (tmp_path / "samples.yaml").write_text(
        "- sample_id: S001\n  name: Alpha\n  site_code: SITE_A\n- sample_id: S002\n  name: Bo\n  site_code: SITE_A\n"
    )
    (tmp_path / "sites.tsv").write_text("site_code\tsite_name\nSITE_A\tBoston Medical\n")

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
              name:
                expr: "{name}[3]"
    """)

    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(TARGET_SCHEMA_YAML)
    tr = ObjectTransformer(unrestricted_eval=False)
    tr.source_schemaview = source_sv
    tr.target_schemaview = target_sv
    tr.create_transformer_specification(yaml.safe_load(spec_yaml))

    loader = DataLoader(tmp_path)

    held_index: LookupIndex | None = None
    with pytest.raises(TransformationError):
        for row in transform_spec(tr, loader):
            if held_index is None:
                held_index = tr.lookup_index
    # First row succeeded → we captured the index. Second row raised → the
    # outer finally must have run cleanup before the exception propagated.
    assert held_index is not None, "expected first row to yield before failure"
    assert tr.lookup_index is None, "owned index must be detached even on exception"
    with pytest.raises((duckdb.ConnectionException, duckdb.InvalidInputException)):
        held_index.register_table("should_fail", tmp_path / "sites.tsv", "site_code")


def test_transform_spec_closes_owned_index_on_early_iterator_close(tmp_path):
    """Cleanup must run when a caller partially consumes and then closes the iterator.

    Python generators run their ``finally`` blocks on ``.close()`` (a
    ``GeneratorExit`` is raised at the suspended ``yield``). The fix
    relies on this — but every other test fully exhausts the iterator,
    so a refactor that broke early-close cleanup would not be caught.
    """
    (tmp_path / "samples.yaml").write_text(
        "- sample_id: S001\n  name: Alpha\n  site_code: SITE_A\n- sample_id: S002\n  name: Beta\n  site_code: SITE_A\n"
    )
    (tmp_path / "sites.tsv").write_text("site_code\tsite_name\nSITE_A\tBoston Medical\n")

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

    # Advance one row, capture the live index, then close the iterator early.
    iterator = transform_spec(tr, loader)
    first = next(iterator)
    assert first["sample_id"] == "S001"
    held_index = tr.lookup_index
    assert held_index is not None, "index should exist after first yield"
    iterator.close()

    # finally must have fired: detached and closed even though we never exhausted.
    assert tr.lookup_index is None, "owned index must be detached on early close"
    with pytest.raises((duckdb.ConnectionException, duckdb.InvalidInputException)):
        held_index.register_table("should_fail", tmp_path / "sites.tsv", "site_code")
