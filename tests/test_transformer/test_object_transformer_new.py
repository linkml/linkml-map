"""Test the object transformer. -- New framework"""

from typing import Any

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer
from tests.scaffold import make_scaffold

@pytest.fixture
def scaffold():
    """Fresh scaffold per test."""
    return make_scaffold()


from tests import (
    PERSONINFO_DATA,
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TGT_DATA,
    PERSONINFO_TGT_SCHEMA,
    PERSONINFO_TR,
)

TARGET_DATA = yaml.safe_load(open(str(PERSONINFO_TGT_DATA)))

def inject_slot(schema_dict: dict, class_name: str, slot_name: str, slot_def: dict):
    schema_dict.setdefault("slots", {})[slot_name] = slot_def
    schema_dict["classes"][class_name].setdefault("slots", []).append(slot_name)

def inject_enum(schema: dict, enum_name: str, values: list[str]) -> None:
    schema["enums"][enum_name] = { "permissible_values": {val: {} for val in values} }

def test_constant_value_slot_derivation_old() -> None:
    """
    Tests transforming using a constant value (via `value:` field).
    """
    source_schema: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_SRC_SCHEMA)))
    # No need to inject a source slot since `value:` doesn't need source data

    target_schema: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_TGT_SCHEMA)))
    inject_slot(target_schema, "Agent", "study_name", {"range": "string"})

    transform_spec: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_TR)))
    transform_spec.setdefault("class_derivations", {}).setdefault("Agent", {}) \
                  .setdefault("slot_derivations", {})["study_name"] = {
                      "value": "Framingham",
                      "range": "string",
                  }

    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = SchemaView(yaml.dump(source_schema))
    obj_tr.target_schemaview = SchemaView(yaml.dump(target_schema))
    obj_tr.create_transformer_specification(transform_spec)

    person_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_DATA)))
    target_dict: dict[str, Any] = obj_tr.map_object(person_dict, source_type="Person")

    expected = dict(TARGET_DATA)
    expected["study_name"] = "Framingham"
    assert target_dict == expected

def test_constant_value_slot_derivation(scaffold):
    # Add extra target slot
    scaffold["target_schema"]["slots"]["study_name"] = {"range": "string"}
    scaffold["target_schema"]["classes"]["Agent"]["slots"].append("study_name")

    # Add constant value derivation
    scaffold["transform_spec"]["class_derivations"]["Agent"]["slot_derivations"]["study_name"] = {
        "value": "Framingham",
        "range": "string"
    }

    # Update expected output
    scaffold["expected"]["study_name"] = "Framingham"

    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = SchemaView(scaffold["source_schema"])
    obj_tr.target_schemaview = SchemaView(scaffold["target_schema"])
    obj_tr.create_transformer_specification(scaffold["transform_spec"])

    result = obj_tr.map_object(scaffold["input_data"], source_type="Person")
    assert result == scaffold["expected"]

