"""Tests for string-to-object range override patterns (Issue #129).

Explores whether linkml-map can handle transformations where a source slot
has ``range: string`` and the target redefines that slot as a structured
object (e.g. ``range: QuantityValue``).

Three scenarios are tested:

A. **Baseline** -- string-to-string passthrough (no range change).
B. **Construct from sub-fields** -- two source string slots are combined
   into a target ``QuantityValue`` via an ``expr`` that builds a dict.
C. **Parse a composite string** -- a single ``"5 m"`` string is split
   inside an ``expr`` to produce a ``QuantityValue``.
"""

from typing import Any

import pytest
from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _source_schema_flat() -> SchemaBuilder:
    """Source schema with separate depth_value / depth_unit string fields."""
    sb = SchemaBuilder()
    sb.add_slot("id", range="string", identifier=True)
    sb.add_slot("depth_value", range="string")
    sb.add_slot("depth_unit", range="string")
    sb.add_class("FlatSample", slots=["id", "depth_value", "depth_unit"])
    sb.add_defaults()
    return sb


def _source_schema_string() -> SchemaBuilder:
    """Source schema with a single depth string (e.g. ``'5 m'``)."""
    sb = SchemaBuilder()
    sb.add_slot("id", range="string", identifier=True)
    sb.add_slot("depth", range="string")
    sb.add_class("StringSample", slots=["id", "depth"])
    sb.add_defaults()
    return sb


def _target_schema_string() -> SchemaBuilder:
    """Target schema where depth remains a plain string."""
    sb = SchemaBuilder()
    sb.add_slot("id", range="string", identifier=True)
    sb.add_slot("depth", range="string")
    sb.add_class("StructuredSample", slots=["id", "depth"])
    sb.add_defaults()
    return sb


def _target_schema_quantity() -> SchemaBuilder:
    """Target schema where depth is a structured QuantityValue."""
    sb = SchemaBuilder()
    sb.add_slot("id", range="string", identifier=True)
    sb.add_slot("has_numeric_value", range="float")
    sb.add_slot("has_unit", range="string")
    sb.add_class("QuantityValue", slots=["has_numeric_value", "has_unit"])
    sb.add_slot("depth", range="QuantityValue", inlined=True)
    sb.add_class("StructuredSample", slots=["id", "depth"])
    sb.add_defaults()
    return sb


# ---------------------------------------------------------------------------
# Transformation specs
# ---------------------------------------------------------------------------

TRANSFORM_PASSTHROUGH: dict[str, Any] = {
    "class_derivations": {
        "StructuredSample": {
            "populated_from": "StringSample",
            "slot_derivations": {
                "id": {},
                "depth": {"populated_from": "depth"},
            },
        },
    },
}

TRANSFORM_CONSTRUCT: dict[str, Any] = {
    "class_derivations": {
        "StructuredSample": {
            "populated_from": "FlatSample",
            "slot_derivations": {
                "id": {},
                "depth": {
                    "expr": (
                        '{"has_numeric_value": float(depth_value),'
                        ' "has_unit": depth_unit}'
                    ),
                },
            },
        },
    },
}

TRANSFORM_PARSE: dict[str, Any] = {
    "class_derivations": {
        "StructuredSample": {
            "populated_from": "StringSample",
            "slot_derivations": {
                "id": {},
                "depth": {
                    "expr": (
                        '{"has_numeric_value": float(depth.split(" ")[0]),'
                        ' "has_unit": depth.split(" ")[1]}'
                    ),
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run(
    source_schema: SchemaBuilder,
    target_schema: SchemaBuilder,
    transform_spec: dict[str, Any],
    input_data: dict[str, Any],
    source_type: str,
) -> dict[str, Any]:
    """Instantiate an ObjectTransformer and map a single object."""
    tr = ObjectTransformer(unrestricted_eval=True)
    tr.source_schemaview = SchemaView(source_schema.schema)
    tr.target_schemaview = SchemaView(target_schema.schema)
    tr.create_transformer_specification(transform_spec)
    return tr.map_object(input_data, source_type=source_type)


# ---------------------------------------------------------------------------
# Test A -- string -> string passthrough (baseline)
# ---------------------------------------------------------------------------

def test_passthrough_string_to_string() -> None:
    """Depth stays a plain string when both schemas use range: string."""
    result = _run(
        source_schema=_source_schema_string(),
        target_schema=_target_schema_string(),
        transform_spec=TRANSFORM_PASSTHROUGH,
        input_data={"id": "samp1", "depth": "5 m"},
        source_type="StringSample",
    )
    assert result == {"id": "samp1", "depth": "5 m"}


# ---------------------------------------------------------------------------
# Test B -- construct QuantityValue from separate sub-fields via expr
# ---------------------------------------------------------------------------

def test_construct_object_from_subfields() -> None:
    """Build a QuantityValue dict from depth_value and depth_unit via expr."""
    result = _run(
        source_schema=_source_schema_flat(),
        target_schema=_target_schema_quantity(),
        transform_spec=TRANSFORM_CONSTRUCT,
        input_data={"id": "samp1", "depth_value": "5", "depth_unit": "m"},
        source_type="FlatSample",
    )
    assert result["id"] == "samp1"
    assert result["depth"] == {
        "has_numeric_value": 5.0,
        "has_unit": "m",
    }


# ---------------------------------------------------------------------------
# Test C -- parse "5 m" string into QuantityValue via expr
# ---------------------------------------------------------------------------

def test_parse_string_into_object() -> None:
    """Parse a composite '5 m' string into a QuantityValue dict via expr."""
    result = _run(
        source_schema=_source_schema_string(),
        target_schema=_target_schema_quantity(),
        transform_spec=TRANSFORM_PARSE,
        input_data={"id": "samp1", "depth": "5 m"},
        source_type="StringSample",
    )
    assert result["id"] == "samp1"
    assert result["depth"] == {
        "has_numeric_value": 5.0,
        "has_unit": "m",
    }
