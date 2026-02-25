"""Test the object transformer. -- New framework"""
import pytest
from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    TransformationSpecification,
)
from linkml_map.transformer.object_transformer import ObjectTransformer
from tests.conftest import add_to_test_setup, TEST_SETUP_FUNCTIONS
from tests.scaffold.utils.apply_patch import apply_schema_patch, apply_transform_patch

def run_transformer(scaffold, source_type="Person"):
    """Helper function to run the object transformer with the given scaffold."""
    source = scaffold["source_schema"]
    target = scaffold["target_schema"]

    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = source
    obj_tr.target_schemaview = target
    obj_tr.create_transformer_specification(scaffold["transform_spec"])

    return obj_tr.map_object(scaffold["input_data"], source_type=source_type)

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


# ---------------------------------------------------------------------------
# Unit tests for _resolve_source_type (extracted from map_object)
# ---------------------------------------------------------------------------

def _make_transformer_with_spec(**kwargs) -> ObjectTransformer:
    """Create a minimal ObjectTransformer with a specification."""
    tr = ObjectTransformer()
    tr.specification = TransformationSpecification(**kwargs)
    return tr


class TestResolveSourceType:
    """Unit tests for ObjectTransformer._resolve_source_type."""

    def test_explicit_source_type_returned_unchanged(self):
        """Return source_type as-is when explicitly provided."""
        tr = _make_transformer_with_spec(
            class_derivations=[ClassDerivation(name="X")],
        )
        assert tr._resolve_source_type("Foo", sv=None) == "Foo"

    def test_no_sv_falls_back_to_first_class_derivation(self):
        """When no sv and no source_type, use first class_derivation name."""
        tr = _make_transformer_with_spec(
            class_derivations=[
                ClassDerivation(name="Alpha"),
                ClassDerivation(name="Beta"),
            ],
        )
        assert tr._resolve_source_type(None, sv=None) == "Alpha"

    def test_sv_with_single_tree_root(self):
        """Resolve to the single tree_root class."""
        sv = SchemaView(
            """
            id: https://example.org/test
            name: test
            imports:
              - linkml:types
            classes:
              Root:
                tree_root: true
              Other: {}
            """
        )
        tr = _make_transformer_with_spec(
            class_derivations=[ClassDerivation(name="Root")],
        )
        assert tr._resolve_source_type(None, sv) == "Root"

    def test_sv_with_multiple_tree_roots_raises(self):
        """Raise ValueError when multiple tree_root classes exist."""
        sv = SchemaView(
            """
            id: https://example.org/test
            name: test
            imports:
              - linkml:types
            classes:
              RootA:
                tree_root: true
              RootB:
                tree_root: true
            """
        )
        tr = _make_transformer_with_spec(
            class_derivations=[ClassDerivation(name="RootA")],
        )
        with pytest.raises(ValueError, match="multiple root classes"):
            tr._resolve_source_type(None, sv)

    def test_sv_with_single_class_no_root(self):
        """Resolve to the only class when no tree_root is set."""
        sv = SchemaView(
            """
            id: https://example.org/test
            name: test
            imports:
              - linkml:types
            classes:
              Only: {}
            """
        )
        tr = _make_transformer_with_spec(
            class_derivations=[ClassDerivation(name="Only")],
        )
        assert tr._resolve_source_type(None, sv) == "Only"

    def test_sv_with_multiple_classes_no_root_raises(self):
        """Raise ValueError when no tree_root and multiple classes."""
        sv = SchemaView(
            """
            id: https://example.org/test
            name: test
            imports:
              - linkml:types
            classes:
              A: {}
              B: {}
            """
        )
        tr = _make_transformer_with_spec(
            class_derivations=[ClassDerivation(name="A")],
        )
        with pytest.raises(ValueError, match="no root classes"):
            tr._resolve_source_type(None, sv)


def test_implicit_source_type_resolution(scaffold):
    """Integration: implicit source_type resolution via tree_root through full transformer."""
    scaffold["source_schema"].schema.classes["Person"].tree_root = True
    result = run_transformer(scaffold, source_type=None)
    assert result == scaffold["expected"]
