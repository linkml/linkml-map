"""Edge-case tests for the transform_spec engine (supplements test_cross_table_lookup.py).

Covers:
- Engine with no-joins class_derivation (regression safety)
- Empty joined table (headers only)
- Mixed derivations: one with joins, one without

See: https://github.com/linkml/linkml-map/pull/136
"""

# ruff: noqa: ANN401, PLR2004

import textwrap

import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.object_transformer import ObjectTransformer


# ---- shared schemas ----

SOURCE_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/engine-test-source
    name: engine_test_source
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
    id: https://example.org/engine-test-target
    name: engine_test_target
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


def _make_transformer(source_sv, target_sv, spec_yaml):
    """Build an ObjectTransformer from inline YAML strings."""
    tr = ObjectTransformer(unrestricted_eval=False)
    tr.source_schemaview = source_sv
    tr.target_schemaview = target_sv
    tr.create_transformer_specification(yaml.safe_load(spec_yaml))
    return tr


# ---- no-joins regression ----


def test_engine_no_joins(tmp_path):
    """transform_spec works for a class_derivation with no joins block.

    This is a regression test ensuring the join machinery doesn't break
    the common case where joins are not used.
    """
    (tmp_path / "samples.tsv").write_text(
        "sample_id\tname\tsite_code\n"
        "S001\tAlpha\tSITE_A\n"
        "S002\tBeta\tSITE_B\n"
    )

    spec = textwrap.dedent("""\
        class_derivations:
          FlatSample:
            populated_from: samples
            slot_derivations:
              sample_id:
                populated_from: sample_id
              name:
                populated_from: name
    """)
    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(TARGET_SCHEMA_YAML)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(tmp_path)

    results = list(transform_spec(tr, loader))

    assert len(results) == 2
    assert results[0]["sample_id"] == "S001"
    assert results[0]["name"] == "Alpha"
    assert results[1]["sample_id"] == "S002"
    assert results[1]["name"] == "Beta"


def test_engine_no_joins_no_data(tmp_path):
    """transform_spec gracefully yields nothing when the data file doesn't exist."""
    spec = textwrap.dedent("""\
        class_derivations:
          FlatSample:
            populated_from: samples
            slot_derivations:
              sample_id:
                populated_from: sample_id
    """)
    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(TARGET_SCHEMA_YAML)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(tmp_path)  # no files in tmp_path

    results = list(transform_spec(tr, loader))
    assert results == []


# ---- empty joined table ----


def test_join_with_empty_secondary_table(tmp_path):
    """When a joined table has headers but no data rows, lookups return None."""
    (tmp_path / "samples.tsv").write_text(
        "sample_id\tname\tsite_code\n"
        "S001\tAlpha\tSITE_A\n"
    )
    # sites.tsv has headers only — no data rows
    (tmp_path / "sites.tsv").write_text("site_code\tsite_name\n")

    spec = textwrap.dedent("""\
        class_derivations:
          FlatSample:
            populated_from: samples
            joins:
              sites:
                join_on: site_code
            slot_derivations:
              sample_id:
                populated_from: sample_id
              name:
                populated_from: name
              site_name:
                expr: "{sites.site_name}"
    """)
    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(TARGET_SCHEMA_YAML)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(tmp_path)

    results = list(transform_spec(tr, loader))

    assert len(results) == 1
    assert results[0]["sample_id"] == "S001"
    assert results[0]["name"] == "Alpha"
    # No matching row in empty sites table → None via null propagation
    assert results[0].get("site_name") is None


# ---- mixed: one derivation with joins, one without ----


def test_mixed_derivations_with_and_without_joins(tmp_path):
    """Multiple class_derivations can coexist: some with joins, some without."""
    (tmp_path / "samples.tsv").write_text(
        "sample_id\tname\tsite_code\n"
        "S001\tAlpha\tSITE_A\n"
    )
    (tmp_path / "sites.tsv").write_text(
        "site_code\tsite_name\n"
        "SITE_A\tBoston Medical\n"
    )

    # Two target classes: one uses joins, one doesn't
    target_yaml = textwrap.dedent("""\
        id: https://example.org/engine-test-target
        name: engine_test_target
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
          SimpleSample:
            attributes:
              sample_id:
                identifier: true
              name: {}
    """)

    spec = textwrap.dedent("""\
        class_derivations:
          FlatSample:
            populated_from: samples
            joins:
              sites:
                join_on: site_code
            slot_derivations:
              sample_id:
                populated_from: sample_id
              name:
                populated_from: name
              site_name:
                expr: "{sites.site_name}"
          SimpleSample:
            populated_from: samples
            slot_derivations:
              sample_id:
                populated_from: sample_id
              name:
                populated_from: name
    """)
    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(target_yaml)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(tmp_path)

    results = list(transform_spec(tr, loader))

    # Should get results from both derivations
    assert len(results) == 2
    # First: FlatSample with join
    assert results[0]["site_name"] == "Boston Medical"
    # Second: SimpleSample without join
    assert results[1]["sample_id"] == "S001"
    assert results[1]["name"] == "Alpha"
