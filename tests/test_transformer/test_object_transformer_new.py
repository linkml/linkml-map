"""Test the object transformer. -- New framework"""
from linkml_runtime.linkml_model import SlotDefinition
import pytest

from linkml_map.transformer.object_transformer import ObjectTransformer
from tests.conftest import add_to_test_setup, TEST_SETUP_FUNCTIONS

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

def add_attribute_to_class(scaffold, class_name, attribute_name, attribute_range):
    """Helper function to add an attribute to a class in the target schema."""
    attribute = SlotDefinition(name=attribute_name, range=attribute_range)
    scaffold["target_schema"].schema.classes[class_name].attributes[attribute_name] = attribute

def add_slot_derivation_to_transform_spec(scaffold, class_name, slot_name, value):
    """Helper function to add a slot derivation to the transform specification."""
    scaffold["transform_spec"]["class_derivations"][class_name]["slot_derivations"][slot_name] = {
        "value": value,
    }

def test_basic_person_to_agent(scaffold):
    """Ensure Person is transformed into Agent with expected slot mappings."""

    result = run_transformer(scaffold)
    assert result == scaffold["expected"]

# Each setup function should adjust the scaffold (schemas, transform spec, and expected output).
# Mark with @add_to_test_setup to include in both parameterized unit tests and integration tests.
#
# @add_to_test_setup
# def setup_your_test_name(scaffold):
#     # Add your test setup code modifying the scaffold here

@add_to_test_setup
def setup_value_slot_derivation(scaffold):
    """Derive slot from constant value."""
    add_slot_to_class(scaffold, class_name="Agent", slot_name="study_name", slot_range="string")
    add_slot_derivation_to_transform_spec(scaffold, class_name="Agent", slot_name="study_name", value="Framingham Heart Study")

    scaffold["expected"]["study_name"] = "Framingham Heart Study"

@add_to_test_setup
def setup_value_attribute_slot_derivation(scaffold):
    """Derive attribute from constant value."""
    add_attribute_to_class(scaffold, class_name="Agent", attribute_name="location", attribute_range="string")
    add_slot_derivation_to_transform_spec(scaffold, class_name="Agent", slot_name="location", value="Framingham")

    scaffold["expected"]["location"] = "Framingham"

@pytest.mark.parametrize(
    "setup_func",
    TEST_SETUP_FUNCTIONS,
    ids=[f.__doc__ or f.__name__.removeprefix("setup_") for f in TEST_SETUP_FUNCTIONS],
)
def test_with_setup(scaffold, setup_func):
    """Apply a setup function, run transformer, and assert expected output."""
    setup_func(scaffold)
    result = run_transformer(scaffold)
    assert result == scaffold["expected"]

def test_all_setup_integration(integration_scaffold):
    result = run_transformer(integration_scaffold)
    assert result == integration_scaffold["expected"]
