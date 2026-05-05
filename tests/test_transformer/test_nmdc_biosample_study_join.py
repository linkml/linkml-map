"""Tests for cross-table Biosample-Study denormalization using joins.

Demonstrates the ``joins:`` feature from PR #136: Biosample rows are
enriched with Study metadata (PI name, ecosystem, study name) by joining
on ``associated_studies``. This is the pattern needed for NMDC lakehouse
tables where biosample rows carry denormalized study context.

This test requires the cross-table join feature introduced in PR #136.

See also:
- PR #136 (cross-table lookup support)
- Issue #134 (cross-table slot lookup design)
"""

# ruff: noqa: PLR2004

import textwrap

import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.object_transformer import ObjectTransformer

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

SOURCE_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/nmdc-join-source
    name: nmdc_join_source
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string
    classes:
      Biosample:
        attributes:
          id:
            identifier: true
          name: {}
          associated_studies: {}
          depth_value: {}
          depth_unit: {}
          env_broad_scale_term_id: {}
          ecosystem: {}
          ecosystem_category: {}
      Study:
        attributes:
          id:
            identifier: true
          name: {}
          pi_name: {}
          pi_email: {}
          ecosystem: {}
          ecosystem_category: {}
          funding_sources: {}
""")

TARGET_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/nmdc-join-target
    name: nmdc_join_target
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string
    classes:
      DenormalizedBiosample:
        attributes:
          biosample_id:
            identifier: true
          biosample_name: {}
          depth_value: {}
          depth_unit: {}
          env_broad_scale_term_id: {}
          ecosystem: {}
          ecosystem_category: {}
          study_id: {}
          study_name: {}
          pi_name: {}
          pi_email: {}
          study_ecosystem: {}
          funding_sources: {}
""")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_transformer(source_sv, target_sv, spec_yaml):
    tr = ObjectTransformer(unrestricted_eval=False)
    tr.source_schemaview = source_sv
    tr.target_schemaview = target_sv
    tr.create_transformer_specification(yaml.safe_load(spec_yaml))
    return tr


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_biosample_study_join(tmp_path):
    """Biosample rows are enriched with Study metadata via join on associated_studies."""
    (tmp_path / "Biosample.tsv").write_text(
        "id\tname\tassociated_studies\tdepth_value\tdepth_unit\t"
        "env_broad_scale_term_id\tecosystem\tecosystem_category\n"
        "nmdc:bsm-12-abc\tHopland soil\tnmdc:sty-11-001\t0.75\tm\t"
        "ENVO:01000174\tEnvironmental\tTerrestrial\n"
        "nmdc:bsm-12-def\tStream sediment\tnmdc:sty-11-002\t1.5\tm\t"
        "ENVO:00002030\tEnvironmental\tAquatic\n"
        "nmdc:bsm-12-ghi\tOrphan sample\tnmdc:sty-11-999\t0.1\tm\t"
        "ENVO:01000174\tEnvironmental\tTerrestrial\n"
    )
    (tmp_path / "Study.tsv").write_text(
        "id\tname\tpi_name\tpi_email\tecosystem\t"
        "ecosystem_category\tfunding_sources\n"
        "nmdc:sty-11-001\tHopland Metagenome\tElaine Faustman\t"
        "faustman@example.org\tEnvironmental\tTerrestrial\tDOE BER\n"
        "nmdc:sty-11-002\tStream Ecology\tJane Doe\t"
        "jdoe@example.org\tEnvironmental\tAquatic\tNSF\n"
    )

    spec = textwrap.dedent("""\
        class_derivations:
          DenormalizedBiosample:
            populated_from: Biosample
            joins:
              Study:
                source_key: associated_studies
                lookup_key: id
            slot_derivations:
              biosample_id:
                populated_from: id
              biosample_name:
                populated_from: name
              depth_value:
                populated_from: depth_value
              depth_unit:
                populated_from: depth_unit
              env_broad_scale_term_id:
                populated_from: env_broad_scale_term_id
              ecosystem:
                populated_from: ecosystem
              ecosystem_category:
                populated_from: ecosystem_category
              study_id:
                expr: "{Study.id}"
              study_name:
                expr: "{Study.name}"
              pi_name:
                expr: "{Study.pi_name}"
              pi_email:
                expr: "{Study.pi_email}"
              study_ecosystem:
                expr: "{Study.ecosystem}"
              funding_sources:
                expr: "{Study.funding_sources}"
    """)

    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(TARGET_SCHEMA_YAML)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(tmp_path)

    results = list(transform_spec(tr, loader))
    assert len(results) == 3

    # Biosample 1: joined to Study 001
    r0 = results[0]
    assert r0["biosample_id"] == "nmdc:bsm-12-abc"
    assert r0["biosample_name"] == "Hopland soil"
    assert str(r0["depth_value"]) == "0.75"
    assert r0["depth_unit"] == "m"
    assert r0["study_id"] == "nmdc:sty-11-001"
    assert r0["study_name"] == "Hopland Metagenome"
    assert r0["pi_name"] == "Elaine Faustman"
    assert r0["pi_email"] == "faustman@example.org"
    assert r0["funding_sources"] == "DOE BER"

    # Biosample 2: joined to Study 002
    r1 = results[1]
    assert r1["biosample_id"] == "nmdc:bsm-12-def"
    assert r1["study_id"] == "nmdc:sty-11-002"
    assert r1["study_name"] == "Stream Ecology"
    assert r1["pi_name"] == "Jane Doe"

    # Biosample 3: orphan — Study 999 doesn't exist → null propagation
    r2 = results[2]
    assert r2["biosample_id"] == "nmdc:bsm-12-ghi"
    assert r2["biosample_name"] == "Orphan sample"
    assert r2.get("study_id") is None
    assert r2.get("study_name") is None
    assert r2.get("pi_name") is None


def test_biosample_study_join_preserves_biosample_fields(tmp_path):
    """All biosample-native fields pass through unchanged when joins are present."""
    (tmp_path / "Biosample.tsv").write_text(
        "id\tname\tassociated_studies\tdepth_value\tdepth_unit\t"
        "env_broad_scale_term_id\tecosystem\tecosystem_category\n"
        "nmdc:bsm-12-xyz\tTest sample\tnmdc:sty-11-001\t2.0\tft\t"
        "ENVO:00002030\tHost-associated\tHuman\n"
    )
    (tmp_path / "Study.tsv").write_text(
        "id\tname\tpi_name\tpi_email\tecosystem\t"
        "ecosystem_category\tfunding_sources\n"
        "nmdc:sty-11-001\tTest Study\tTest PI\t"
        "test@example.org\tEnvironmental\tTerrestrial\tDOE\n"
    )

    spec = textwrap.dedent("""\
        class_derivations:
          DenormalizedBiosample:
            populated_from: Biosample
            joins:
              Study:
                source_key: associated_studies
                lookup_key: id
            slot_derivations:
              biosample_id:
                populated_from: id
              biosample_name:
                populated_from: name
              depth_value:
                populated_from: depth_value
              depth_unit:
                populated_from: depth_unit
              env_broad_scale_term_id:
                populated_from: env_broad_scale_term_id
              ecosystem:
                populated_from: ecosystem
              ecosystem_category:
                populated_from: ecosystem_category
              study_id:
                expr: "{Study.id}"
              study_name:
                expr: "{Study.name}"
              pi_name:
                expr: "{Study.pi_name}"
              pi_email:
                expr: "{Study.pi_email}"
              study_ecosystem:
                expr: "{Study.ecosystem}"
              funding_sources:
                expr: "{Study.funding_sources}"
    """)

    source_sv = SchemaView(SOURCE_SCHEMA_YAML)
    target_sv = SchemaView(TARGET_SCHEMA_YAML)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(tmp_path)

    results = list(transform_spec(tr, loader))
    assert len(results) == 1

    r = results[0]
    # All biosample fields preserved
    assert r["biosample_id"] == "nmdc:bsm-12-xyz"
    assert r["biosample_name"] == "Test sample"
    assert str(r["depth_value"]) == "2.0"
    assert r["depth_unit"] == "ft"
    assert r["env_broad_scale_term_id"] == "ENVO:00002030"
    assert r["ecosystem"] == "Host-associated"
    assert r["ecosystem_category"] == "Human"
    # Study fields joined
    assert r["study_id"] == "nmdc:sty-11-001"
    assert r["pi_name"] == "Test PI"
