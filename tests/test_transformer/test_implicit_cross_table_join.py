"""Tests for implicit cross-table join resolution (#212).

When a nested class_derivation has a different populated_from than its parent
and no explicit joins: block, the transformer should:
1. Find common columns between the two source classes
2. Auto-resolve the join on that column
3. Allow slot derivations to reference columns from either table
4. Error on ambiguous columns (present in both) without dot notation
5. Error when no common columns exist
"""

import csv
import textwrap

import pytest
import yaml

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.session import Session
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.errors import TransformationError

SOURCE_SCHEMA = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/implicit-join-test
    name: implicit_join_test
    prefixes:
      linkml: https://w3id.org/linkml/
      xsd: http://www.w3.org/2001/XMLSchema#
    default_prefix: implicit_join_test
    default_range: string
    imports:
      - linkml:types

    classes:
      Measurement:
        attributes:
          id:
            identifier: true
          subject_id:
            range: string
          method:
            range: string

      Reading:
        attributes:
          id:
            identifier: true
          subject_id:
            range: string
          score:
            range: float
""")
)

# Same as above but Reading also has a "method" column (ambiguous with Measurement)
SOURCE_SCHEMA_AMBIGUOUS = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/implicit-join-test-ambiguous
    name: implicit_join_test_ambiguous
    prefixes:
      linkml: https://w3id.org/linkml/
      xsd: http://www.w3.org/2001/XMLSchema#
    default_prefix: implicit_join_test_ambiguous
    default_range: string
    imports:
      - linkml:types

    classes:
      Measurement:
        attributes:
          id:
            identifier: true
          subject_id:
            range: string
          method:
            range: string

      Reading:
        attributes:
          id:
            identifier: true
          subject_id:
            range: string
          method:
            range: string
          score:
            range: float
""")
)


TRANSFORM_SPEC = yaml.safe_load(
    textwrap.dedent("""\
    id: implicit-join-transform
    title: Implicit cross-table join

    class_derivations:
      Result:
        populated_from: Measurement
        slot_derivations:
          id:
          method:
          observation:
            class_derivations:
              - Observation:
                  populated_from: Reading
                  slot_derivations:
                    value:
                      populated_from: score
""")
)

TARGET_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/implicit-join-target
    name: implicit_join_target
    prefixes:
      linkml: https://w3id.org/linkml/
      xsd: http://www.w3.org/2001/XMLSchema#
    default_prefix: implicit_join_target
    default_range: string
    imports:
      - linkml:types

    classes:
      Result:
        attributes:
          id:
            identifier: true
          method:
            range: string
          observation:
            range: Observation
            inlined: true

      Observation:
        attributes:
          value:
            range: float
""")


@pytest.fixture()
def data_dir(tmp_path):
    """Create TSV files for Measurement and Reading tables."""
    measurement_path = tmp_path / "Measurement.tsv"
    with open(measurement_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "M1", "subject_id": "S1", "method": "spirometry"})
        writer.writerow({"id": "M2", "subject_id": "S2", "method": "peak_flow"})

    reading_path = tmp_path / "Reading.tsv"
    with open(reading_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "score"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "R1", "subject_id": "S1", "score": "95.5"})
        writer.writerow({"id": "R2", "subject_id": "S2", "score": "88.0"})

    return tmp_path


@pytest.fixture()
def data_dir_ambiguous(tmp_path):
    """Create TSV files where Reading also has a method column."""
    measurement_path = tmp_path / "Measurement.tsv"
    with open(measurement_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "M1", "subject_id": "S1", "method": "spirometry"})

    reading_path = tmp_path / "Reading.tsv"
    with open(reading_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method", "score"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "R1", "subject_id": "S1", "method": "peak_flow", "score": "95.5"})

    return tmp_path


def _make_transformer(source_schema, transform_spec_dict, target_schema_yaml=None):
    """Create a configured ObjectTransformer."""
    session = Session()
    session.set_source_schema(source_schema)
    session.set_object_transformer(transform_spec_dict)
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    if target_schema_yaml:
        from linkml_runtime import SchemaView

        tr.target_schemaview = SchemaView(target_schema_yaml)
    else:
        tr.target_schemaview = session.target_schemaview
    return tr


def test_implicit_join_resolves_via_engine(data_dir):
    """Engine mode: implicit join on common column 'subject_id' resolves nested values."""
    tr = _make_transformer(SOURCE_SCHEMA, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 2

    r1 = results[0]
    assert r1["id"] == "M1"
    assert r1["method"] == "spirometry"
    assert r1["observation"]["value"] == 95.5

    r2 = results[1]
    assert r2["id"] == "M2"
    assert r2["method"] == "peak_flow"
    assert r2["observation"]["value"] == 88.0


def test_implicit_join_ambiguous_columns_resolved_when_one_non_id(data_dir):
    """When both tables share 'id' (identifier) and 'subject_id' (non-id), join on subject_id.

    Ambiguous non-data columns (like 'id') that are identifiers get excluded,
    leaving 'subject_id' as the sole non-id common column.
    """
    tr = _make_transformer(SOURCE_SCHEMA, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 2
    # id columns are ambiguous (both tables have them), but subject_id is the join key
    # The nested row's 'score' should be resolved
    assert results[0]["observation"]["value"] == 95.5
    assert results[1]["observation"]["value"] == 88.0


def test_implicit_join_no_common_columns(data_dir):
    """Error when no common columns exist between parent and nested tables."""
    schema_no_common = yaml.safe_load(
        textwrap.dedent("""\
        id: https://example.org/no-common
        name: no_common
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: no_common
        default_range: string
        imports:
          - linkml:types
        classes:
          Measurement:
            attributes:
              id:
                identifier: true
              method:
                range: string
          Reading:
            attributes:
              reading_id:
                identifier: true
              score:
                range: float
    """)
    )

    tr = _make_transformer(schema_no_common, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    with pytest.raises(TransformationError, match="no common columns"):
        list(transform_spec(tr, data_loader, source_type="Measurement"))


def test_implicit_join_multiple_non_id_common_columns(data_dir_ambiguous):
    """Error when multiple non-identifier common columns exist (ambiguous join key)."""
    schema_multi_common = yaml.safe_load(
        textwrap.dedent("""\
        id: https://example.org/multi-common
        name: multi_common
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: multi_common
        default_range: string
        imports:
          - linkml:types
        classes:
          Measurement:
            attributes:
              id:
                identifier: true
              subject_id:
                range: string
              method:
                range: string
          Reading:
            attributes:
              id:
                identifier: true
              subject_id:
                range: string
              method:
                range: string
              score:
                range: float
    """)
    )

    tr = _make_transformer(schema_multi_common, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir_ambiguous)

    with pytest.raises(TransformationError, match="Multiple common columns"):
        list(transform_spec(tr, data_loader, source_type="Measurement"))
