"""Tests for deterministic ID generation using uuid5() in transformation expressions.

NMDC uses typed identifiers with a specific pattern: ``nmdc:{typecode}-{shoulder}-{blade}``.
For lakehouse ETL where the same source data is re-processed, deterministic IDs ensure
idempotent results. The ``uuid5()`` function in linkml-map (#117) enables this.

``uuid5(namespace_url, name_string)`` produces a deterministic UUID from a namespace
and a name. By using a fixed namespace and composing the name from source fields,
the same input always produces the same output ID.
"""

import copy
import uuid

from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = """\
id: https://example.org/ext-source
name: ext_source
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  SourceRecord:
    attributes:
      source_db:
        range: string
      source_id:
        identifier: true
        range: string
      sample_name:
        range: string
"""

TARGET_SCHEMA = """\
id: https://example.org/nmdc-target
name: nmdc_target
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Biosample:
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      description:
        range: string
"""

TRANSFORM_SPEC = {
    "class_derivations": {
        "Biosample": {
            "populated_from": "SourceRecord",
            "slot_derivations": {
                "id": {
                    "expr": "'nmdc:bsm-' + uuid5('https://w3id.org/nmdc/', {source_db} + ':' + {source_id})",
                },
                "name": {"populated_from": "sample_name"},
                "description": {
                    "expr": "'Sample from ' + {source_db} + ' study ' + {source_id}",
                },
            },
        }
    }
}


def _make_transformer():
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(copy.deepcopy(TRANSFORM_SPEC))
    return tr


def test_uuid5_deterministic():
    """Same input produces the same ID every time."""
    tr = _make_transformer()
    source = {"source_db": "GOLD", "source_id": "Gb0001234", "sample_name": "Forest soil"}

    result1 = tr.map_object(source, source_type="SourceRecord")
    result2 = tr.map_object(source, source_type="SourceRecord")

    assert result1["id"] == result2["id"]
    assert result1["id"].startswith("nmdc:bsm-")


def test_uuid5_different_inputs_different_ids():
    """Different source records produce different IDs."""
    tr = _make_transformer()

    result_a = tr.map_object(
        {"source_db": "GOLD", "source_id": "Gb0001234", "sample_name": "A"},
        source_type="SourceRecord",
    )
    result_b = tr.map_object(
        {"source_db": "GOLD", "source_id": "Gb0005678", "sample_name": "B"},
        source_type="SourceRecord",
    )

    assert result_a["id"] != result_b["id"]


def test_uuid5_matches_python_stdlib():
    """The uuid5 output matches Python's uuid.uuid5 for the same inputs."""
    tr = _make_transformer()
    source = {"source_db": "GOLD", "source_id": "Gb0001234", "sample_name": "Test"}

    result = tr.map_object(source, source_type="SourceRecord")

    # Compute expected UUID using stdlib
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, "https://w3id.org/nmdc/")
    expected_uuid = str(uuid.uuid5(namespace, "GOLD:Gb0001234"))
    expected_id = f"nmdc:bsm-{expected_uuid}"

    assert result["id"] == expected_id


def test_uuid5_with_string_concatenation():
    """Description field uses string concatenation with source fields."""
    tr = _make_transformer()
    source = {"source_db": "GOLD", "source_id": "Gb0001234", "sample_name": "Forest soil"}

    result = tr.map_object(source, source_type="SourceRecord")

    assert result["name"] == "Forest soil"
    assert result["description"] == "Sample from GOLD study Gb0001234"


def test_uuid5_null_source_field():
    """When a source field used in uuid5 is None, null propagation kicks in."""
    tr = _make_transformer()
    source = {"source_db": None, "source_id": "Gb0001234", "sample_name": "Test"}

    result = tr.map_object(source, source_type="SourceRecord")

    # {source_db} is None → null propagation → entire expr is None
    assert result["id"] is None
