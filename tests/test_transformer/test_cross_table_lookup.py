"""Integration tests for cross-table join lookups (Issue #134).

These tests exercise the full stack: DataLoader → LookupIndex → Bindings →
ObjectTransformer → engine.transform_spec.  Temporary TSV files serve as
primary and secondary tables.
"""

# ruff: noqa: ANN401, PLR2004

import textwrap

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.object_transformer import ObjectTransformer


# ---- fixtures ----

SOURCE_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/cross-table-source
    name: cross_table_source
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string
    classes:
      lab_results:
        attributes:
          sample_id:
            identifier: true
          participant_id: {}
          analyte: {}
          result_value: {}
      demographics:
        attributes:
          participant_id:
            identifier: true
          age_at_exam: {}
          sex: {}
      site_info:
        attributes:
          site_code:
            identifier: true
          site_name: {}
""")

TARGET_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/cross-table-target
    name: cross_table_target
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string
    classes:
      MeasurementObservation:
        attributes:
          sample_id:
            identifier: true
          analyte_value: {}
          age_at_observation: {}
          participant_sex: {}
          site_name: {}
""")


@pytest.fixture()
def data_dir(tmp_path):
    """Write TSV data files and return the directory path."""
    lab = tmp_path / "lab_results.tsv"
    lab.write_text(
        "sample_id\tparticipant_id\tanalyte\tresult_value\n"
        "S001\tP001\tglucose\t5.5\n"
        "S002\tP002\tcholesterol\t200\n"
        "S003\tP999\tglucose\t6.1\n"  # P999 has no demographics row
    )
    demo = tmp_path / "demographics.tsv"
    demo.write_text(
        "participant_id\tage_at_exam\tsex\n"
        "P001\t30\tF\n"
        "P002\t45\tM\n"
    )
    site = tmp_path / "site_info.tsv"
    site.write_text(
        "site_code\tsite_name\n"
        "SITE_A\tBoston Medical\n"
    )
    return tmp_path


@pytest.fixture()
def source_sv():
    return SchemaView(SOURCE_SCHEMA_YAML)


@pytest.fixture()
def target_sv():
    return SchemaView(TARGET_SCHEMA_YAML)


def _make_transformer(source_sv, target_sv, spec_yaml):
    """Build an ObjectTransformer from inline YAML strings."""
    tr = ObjectTransformer(unrestricted_eval=False)
    tr.source_schemaview = source_sv
    tr.target_schemaview = target_sv
    tr.create_transformer_specification(yaml.safe_load(spec_yaml))
    return tr


# ---- tests ----


def test_cross_table_on_shorthand(data_dir, source_sv, target_sv):
    """Cross-table lookup using the `on` shorthand (same column name in both tables)."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              analyte_value:
                populated_from: result_value
              age_at_observation:
                expr: "{demographics.age_at_exam}"
              participant_sex:
                expr: "{demographics.sex}"
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    assert len(results) == 3

    # S001 → P001 → age 30, sex F
    r0 = results[0]
    assert r0["sample_id"] == "S001"
    assert str(r0["analyte_value"]) == "5.5"
    assert r0["age_at_observation"] == "30"
    assert r0["participant_sex"] == "F"

    # S002 → P002 → age 45, sex M
    r1 = results[1]
    assert r1["sample_id"] == "S002"
    assert r1["age_at_observation"] == "45"
    assert r1["participant_sex"] == "M"


def test_cross_table_explicit_keys(data_dir, source_sv, target_sv):
    """Cross-table lookup with explicit source_key and lookup_key."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                source_key: participant_id
                lookup_key: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                expr: "{demographics.age_at_exam}"
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    assert results[0]["age_at_observation"] == "30"
    assert results[1]["age_at_observation"] == "45"


def test_null_propagation_no_match(data_dir, source_sv, target_sv):
    """When the lookup table has no matching row, {table.col} propagates None."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                expr: "{demographics.age_at_exam}"
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    # S003 → P999 → no demographics row → None
    r2 = results[2]
    assert r2["sample_id"] == "S003"
    assert r2.get("age_at_observation") is None


def test_expression_with_joined_column(data_dir, source_sv, target_sv):
    """Expressions can combine joined columns with arithmetic."""
    # Override target schema to use integer range
    target_yaml = textwrap.dedent("""\
        id: https://example.org/cross-table-target
        name: cross_table_target
        prefixes:
          linkml: https://w3id.org/linkml/
        imports:
          - linkml:types
        default_range: string
        classes:
          MeasurementObservation:
            attributes:
              sample_id:
                identifier: true
              age_at_observation:
                range: integer
    """)
    t_sv = SchemaView(target_yaml)

    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                expr: "int({demographics.age_at_exam}) * 365"
    """)
    tr = _make_transformer(source_sv, t_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    assert results[0]["age_at_observation"] == 30 * 365
    assert results[1]["age_at_observation"] == 45 * 365
    # P999 → null propagation through int() would raise, but {..} catches it first
    assert results[2].get("age_at_observation") is None


def test_multiple_joined_tables(data_dir, source_sv, target_sv, tmp_path):
    """Multiple secondary tables can be joined in a single class_derivation."""
    # Add a site_code column to lab_results
    lab = tmp_path / "lab_results.tsv"
    lab.write_text(
        "sample_id\tparticipant_id\tanalyte\tresult_value\tsite_code\n"
        "S001\tP001\tglucose\t5.5\tSITE_A\n"
    )
    # Copy demographics and site_info to tmp_path (already in data_dir fixture)
    (tmp_path / "demographics.tsv").write_text(
        "participant_id\tage_at_exam\tsex\n"
        "P001\t30\tF\n"
    )
    (tmp_path / "site_info.tsv").write_text(
        "site_code\tsite_name\n"
        "SITE_A\tBoston Medical\n"
    )

    # Extend source schema to include site_code on lab_results
    src_yaml = textwrap.dedent("""\
        id: https://example.org/cross-table-source
        name: cross_table_source
        prefixes:
          linkml: https://w3id.org/linkml/
        imports:
          - linkml:types
        default_range: string
        classes:
          lab_results:
            attributes:
              sample_id:
                identifier: true
              participant_id: {}
              analyte: {}
              result_value: {}
              site_code: {}
          demographics:
            attributes:
              participant_id:
                identifier: true
              age_at_exam: {}
              sex: {}
          site_info:
            attributes:
              site_code:
                identifier: true
              site_name: {}
    """)
    s_sv = SchemaView(src_yaml)

    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
              site_info:
                source_key: site_code
                lookup_key: site_code
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                expr: "{demographics.age_at_exam}"
              participant_sex:
                expr: "{demographics.sex}"
              site_name:
                expr: "{site_info.site_name}"
    """)
    tr = _make_transformer(s_sv, target_sv, spec)
    loader = DataLoader(tmp_path)
    results = list(transform_spec(tr, loader))

    assert len(results) == 1
    assert results[0]["age_at_observation"] == "30"
    assert results[0]["participant_sex"] == "F"
    assert results[0]["site_name"] == "Boston Medical"


def test_join_spec_missing_key_raises(source_sv, target_sv, data_dir):
    """A join spec with neither `on` nor source_key/lookup_key raises ValueError."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics: {}
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                expr: "{demographics.age_at_exam}"
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    with pytest.raises(ValueError, match="must specify"):
        list(transform_spec(tr, loader))


# ---- populated_from cross-table tests ----


def test_populated_from_cross_table(data_dir, source_sv, target_sv):
    """populated_from: table.field resolves via join spec + LookupIndex."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                populated_from: demographics.age_at_exam
              participant_sex:
                populated_from: demographics.sex
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    assert len(results) == 3

    # S001 → P001 → age 30, sex F
    assert results[0]["sample_id"] == "S001"
    assert results[0]["age_at_observation"] == "30"
    assert results[0]["participant_sex"] == "F"

    # S002 → P002 → age 45, sex M
    assert results[1]["sample_id"] == "S002"
    assert results[1]["age_at_observation"] == "45"
    assert results[1]["participant_sex"] == "M"


def test_populated_from_cross_table_no_match(data_dir, source_sv, target_sv):
    """When join key has no match in secondary table, populated_from returns None."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                populated_from: demographics.age_at_exam
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    # S003 → P999 → no demographics row → None
    assert results[2]["sample_id"] == "S003"
    assert results[2].get("age_at_observation") is None


def test_populated_from_cross_table_missing_field(data_dir, source_sv, target_sv):
    """When joined row exists but the requested field doesn't, return None."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              nonexistent:
                populated_from: demographics.nonexistent_column
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    assert results[0]["sample_id"] == "S001"
    assert results[0].get("nonexistent") is None


def test_populated_from_with_value_mappings(data_dir, source_sv, target_sv):
    """Cross-table populated_from values flow through value_mappings."""
    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              participant_sex:
                populated_from: demographics.sex
                value_mappings:
                  F:
                    value: Female
                  M:
                    value: Male
    """)
    tr = _make_transformer(source_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    assert results[0]["participant_sex"] == "Female"  # F → Female
    assert results[1]["participant_sex"] == "Male"  # M → Male


def test_populated_from_join_priority_over_fk(data_dir, source_sv, target_sv):
    """When a join name matches a potential FK slot, the join takes priority."""
    # Use a schema where 'demographics' could be an FK slot on lab_results
    # (slot named 'demographics' with range pointing to demographics class).
    # The join should still win.
    fk_schema_yaml = textwrap.dedent("""\
        id: https://example.org/fk-test
        name: fk_test
        prefixes:
          linkml: https://w3id.org/linkml/
        imports:
          - linkml:types
        default_range: string
        classes:
          lab_results:
            attributes:
              sample_id:
                identifier: true
              participant_id: {}
              demographics:
                range: demographics
              result_value: {}
          demographics:
            attributes:
              participant_id:
                identifier: true
              age_at_exam: {}
              sex: {}
    """)
    s_sv = SchemaView(fk_schema_yaml)

    spec = textwrap.dedent("""\
        class_derivations:
          MeasurementObservation:
            populated_from: lab_results
            joins:
              demographics:
                join_on: participant_id
            slot_derivations:
              sample_id:
                populated_from: sample_id
              age_at_observation:
                populated_from: demographics.age_at_exam
    """)
    tr = _make_transformer(s_sv, target_sv, spec)
    loader = DataLoader(data_dir)
    results = list(transform_spec(tr, loader))

    # Should use join (LookupIndex), not FK resolution (object_index)
    assert results[0]["age_at_observation"] == "30"
    assert results[1]["age_at_observation"] == "45"
