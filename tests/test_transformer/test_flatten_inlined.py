"""Tests for flattening inlined objects (QuantityValue pattern) to scalar columns.

Verifies that dot-notation ``expr`` in slot derivations can reach into
inlined composite objects and extract individual fields into flat
target slots.  This is the canonical pattern for converting NMDC-style
QuantityValue composites into simple value+unit columns.

See: https://github.com/linkml/linkml-map/issues/128
"""

import copy

import pytest
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = """\
id: https://example.org/sample-source
name: sample-source
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Sample:
    tree_root: true
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      depth:
        range: QuantityValue
        inlined: true
      elev:
        range: QuantityValue
        inlined: true
  QuantityValue:
    attributes:
      has_numeric_value:
        range: float
      has_unit:
        range: string
"""

TARGET_SCHEMA = """\
id: https://example.org/sample-flat
name: sample-flat
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  FlatSample:
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      depth_value:
        range: float
      depth_unit:
        range: string
      elev_value:
        range: float
      elev_unit:
        range: string
"""

TRANSFORM_SPEC = {
    "class_derivations": {
        "FlatSample": {
            "populated_from": "Sample",
            "slot_derivations": {
                "id": {},
                "name": {},
                "depth_value": {"expr": "depth.has_numeric_value"},
                "depth_unit": {"expr": "depth.has_unit"},
                "elev_value": {"expr": "elev.has_numeric_value"},
                "elev_unit": {"expr": "elev.has_unit"},
            },
        }
    }
}


def _make_transformer() -> ObjectTransformer:
    """Build an ObjectTransformer wired to the source/target schemas and spec."""
    obj_tr = ObjectTransformer()
    obj_tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    obj_tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    obj_tr.create_transformer_specification(copy.deepcopy(TRANSFORM_SPEC))
    return obj_tr


def test_flatten_complete_quantity_values():
    """Both depth and elev are fully populated QuantityValue objects."""
    obj_tr = _make_transformer()

    source = {
        "id": "samp001",
        "name": "Forest soil sample",
        "depth": {"has_numeric_value": 5.0, "has_unit": "m"},
        "elev": {"has_numeric_value": 100.0, "has_unit": "m"},
    }
    result = obj_tr.map_object(source, source_type="Sample")

    assert result["id"] == "samp001"
    assert result["name"] == "Forest soil sample"
    assert result["depth_value"] == 5.0
    assert result["depth_unit"] == "m"
    assert result["elev_value"] == 100.0
    assert result["elev_unit"] == "m"


def test_flatten_null_quantity_value():
    """depth is None; its derived slots should be None."""
    obj_tr = _make_transformer()

    source = {
        "id": "samp002",
        "name": "Lake sediment",
        "depth": None,
        "elev": {"has_numeric_value": 50.0, "has_unit": "m"},
    }
    result = obj_tr.map_object(source, source_type="Sample")

    assert result["id"] == "samp002"
    assert result["depth_value"] is None
    assert result["depth_unit"] is None
    assert result["elev_value"] == 50.0
    assert result["elev_unit"] == "m"


def test_flatten_partial_quantity_value():
    """depth has has_numeric_value but no has_unit."""
    obj_tr = _make_transformer()

    source = {
        "id": "samp003",
        "name": "Stream water",
        "depth": {"has_numeric_value": 2.5},
        "elev": {"has_numeric_value": 300.0, "has_unit": "ft"},
    }
    result = obj_tr.map_object(source, source_type="Sample")

    assert result["id"] == "samp003"
    assert result["depth_value"] == 2.5
    assert result["depth_unit"] is None
    assert result["elev_value"] == 300.0
    assert result["elev_unit"] == "ft"


@pytest.mark.parametrize(
    "depth_input",
    [None, {"has_numeric_value": 7.0, "has_unit": "m"}],
    ids=["null", "populated"],
)
def test_flatten_id_and_name_always_propagate(depth_input):
    """id and name propagate regardless of whether inlined objects are present."""
    obj_tr = _make_transformer()

    source = {
        "id": "samp004",
        "name": "Generic sample",
        "depth": depth_input,
        "elev": None,
    }
    result = obj_tr.map_object(source, source_type="Sample")

    assert result["id"] == "samp004"
    assert result["name"] == "Generic sample"
