"""Test the object transformer. -- New framework"""
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ClassDefinition, SlotDefinition
import pytest
import yaml

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

def apply_schema_patch(schemaview: SchemaView, yaml_str: str):
    """Patch a SchemaView.schema from a YAML fragment."""
    patch = yaml.safe_load(yaml_str)
    schema = schemaview.schema

    # Classes
    for cname, cpatch in patch.get("classes", {}).items():
        if cname not in schema.classes:
            schema.classes[cname] = ClassDefinition(name=cname, **{k: v for k, v in cpatch.items() if k != "slots"})
        existing = schema.classes[cname]
        for slot in cpatch.get("slots", []):
            if slot not in existing.slots:
                existing.slots.append(slot)

    # Slots
    for sname, spatch in patch.get("slots", {}).items():
        if sname not in schema.slots:
            schema.slots[sname] = SlotDefinition(name=sname, **spatch)
        else:
            existing = schema.slots[sname]
            for field, value in spatch.items():
                setattr(existing, field, value)

def apply_transform_patch(transform: dict, yaml_str: str):
    """Merge a YAML fragment into the scaffold['transform_spec']."""
    patch = yaml.safe_load(yaml_str) or {}

    def merge(d, p):
        for k, v in p.items():
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                merge(d[k], v)
            elif isinstance(v, list) and isinstance(d.get(k), list):
                d[k].extend(v)
            else:
                d[k] = v

    merge(transform, patch)
    return transform

def test_basic_person_to_agent(scaffold):
    """Ensure Person is transformed into Agent with expected slot mappings."""

    result = run_transformer(scaffold)
    assert result == scaffold["expected"]

# Each setup function should adjust the scaffold (schemas, transform spec, and expected output).
# Mark with @add_to_test_setup to include in both parameterized unit tests and integration tests.
#
# @add_to_test_setup
# def setup_your_test_name(scaffold):
#     # Your test setup code modifying the scaffold here
#     # apply_schema_patch(...) (source and target)
#     # apply_transform_patch(...)
#     # scaffold["expected"]...

@add_to_test_setup
def setup_value_slot_derivation(scaffold):
    """Derive slot from constant value."""

    apply_schema_patch(scaffold["target_schema"],
"""
    classes:
      Agent:
        slots:
          - study_name
    slots:
      study_name:
        range: string
"""
    )

    apply_transform_patch(scaffold["transform_spec"],
"""
    class_derivations:
      Agent:
        slot_derivations:
          study_name:
            value: Framingham Heart Study
"""
    )

    scaffold["expected"]["study_name"] = "Framingham Heart Study"

@add_to_test_setup
def setup_value_attribute_slot_derivation(scaffold):
    """Derive attribute from constant value."""
    apply_schema_patch(scaffold["target_schema"],
"""
    classes:
      Agent:
        attributes:
          location:
            range: string
"""
    )
    apply_transform_patch(scaffold["transform_spec"],
"""
    class_derivations:
      Agent:
        slot_derivations:
          location:
            value: Framingham
""")

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
