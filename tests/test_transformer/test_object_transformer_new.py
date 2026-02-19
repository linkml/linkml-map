"""Test the object transformer. -- New framework"""
import pytest

from linkml_map.transformer.object_transformer import ObjectTransformer
from tests.conftest import add_to_test_setup, TEST_SETUP_FUNCTIONS
from tests.scaffold.utils.apply_patch import apply_schema_patch, apply_transform_patch

def run_transformer(scaffold):
    """Helper function to run the object transformer with the given scaffold."""
    source = scaffold["source_schema"]
    target = scaffold["target_schema"]

    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = source
    obj_tr.target_schemaview = target
    obj_tr.create_transformer_specification(scaffold["transform_spec"])

    return obj_tr.map_object(scaffold["input_data"], source_type="Person")

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

@add_to_test_setup
def setup_uuid5_expr(scaffold):
    """Derive slot via uuid5 expression."""

    apply_schema_patch(scaffold["target_schema"],
"""
    classes:
      Agent:
        slots:
          - uuid_id
    slots:
      uuid_id:
        range: string
"""
    )

    apply_transform_patch(scaffold["transform_spec"],
"""
    class_derivations:
      Agent:
        slot_derivations:
          uuid_id:
            expr: 'uuid5("https://example.org/Agent", {id})'
"""
    )

    scaffold["expected"]["uuid_id"] = "abbe798e-d61b-5371-86f2-ea8e54129a50"

@pytest.mark.parametrize(
    "setup_func",
    TEST_SETUP_FUNCTIONS,
    ids=[f.__doc__ or f.__name__.removeprefix("setup_") for f in TEST_SETUP_FUNCTIONS],
)
def test_unit(scaffold, setup_func):
    """Apply a setup function, run transformer, and assert expected output."""
    setup_func(scaffold)
    result = run_transformer(scaffold)
    assert result == scaffold["expected"]

def test_integration(integration_scaffold):
    result = run_transformer(integration_scaffold)
    assert result == integration_scaffold["expected"]
