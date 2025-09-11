"""Test the object transformer. -- New framework"""
import pytest
from linkml_runtime.linkml_model import SlotDefinition

from linkml_map.transformer.object_transformer import ObjectTransformer
from tests.conftest import add_to_integration, setup_integration
from tests.scaffold import new_scaffold

@pytest.fixture
def scaffold():
    """Fresh scaffold per test."""
    return new_scaffold()

def run_transformer(scaffold):
    """Helper function to run the object transformer with the given scaffold."""
    source = scaffold["source_schema"]
    target = scaffold["target_schema"]

    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = source
    obj_tr.target_schemaview = target
    obj_tr.create_transformer_specification(scaffold["transform_spec"])

    return obj_tr.map_object(scaffold["input_data"], source_type="Person")

def add_slot_to_class(scaffold, class_name, slot_name, slot_range):
    """Helper function to add a slot to a class in the target schema."""
    scaffold["target_schema"].schema.slots[slot_name] = SlotDefinition(name=slot_name, range=slot_range)
    scaffold["target_schema"].schema.classes[class_name].slots.append(slot_name)

def test_basic_person_to_agent(scaffold):
    """Ensure Person is transformed into Agent with expected slot mappings."""

    result = run_transformer(scaffold)
    assert result == scaffold["expected"]

@add_to_integration
def setup_value_slot_derivation(scaffold):
    # Add study_name slot to target schema
    add_slot_to_class(scaffold, "Agent", "study_name", "string")

    # Add value slot_derivation
    scaffold["transform_spec"]["class_derivations"]["Agent"]["slot_derivations"]["study_name"] = {
        "value": "Framingham",
    }

    # Update expected output
    scaffold["expected"]["study_name"] = "Framingham"

def test_value_slot_derivation(scaffold):
    setup_value_slot_derivation(scaffold)

    result = run_transformer(scaffold)
    assert result == scaffold["expected"]

def test_z_integration(scaffold):
    setup_integration(scaffold)

    result = run_transformer(scaffold)
    assert result == scaffold["expected"]
