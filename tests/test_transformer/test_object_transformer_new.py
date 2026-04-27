"""Test the object transformer. -- New framework"""

import pytest
from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    TransformationSpecification,
)
from linkml_map.transformer.object_transformer import ObjectTransformer
from tests.conftest import TEST_SETUP_FUNCTIONS, add_to_test_setup
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

    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        slots:
          - study_name
    slots:
      study_name:
        range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          study_name:
            value: Framingham Heart Study
""",
    )

    scaffold["expected"]["study_name"] = "Framingham Heart Study"


@add_to_test_setup
def setup_value_attribute_slot_derivation(scaffold):
    """Derive attribute from constant value."""
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        attributes:
          location:
            range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          location:
            value: Framingham
""",
    )

    scaffold["expected"]["location"] = "Framingham"


@add_to_test_setup
def setup_uuid5_expr(scaffold):
    """Derive slot via uuid5 expression."""

    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        slots:
          - uuid_id
    slots:
      uuid_id:
        range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          uuid_id:
            expr: 'uuid5("https://example.org/Agent", {id})'
""",
    )

    scaffold["expected"]["uuid_id"] = "abbe798e-d61b-5371-86f2-ea8e54129a50"


@add_to_test_setup
def setup_slot_fn_basic(scaffold):
    """Reference a previously derived slot via slot()."""
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        slots:
          - name_length
          - name_length_copy
    slots:
      name_length:
        range: integer
      name_length_copy:
        range: integer
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          name_length:
            expr: "strlen({name})"
          name_length_copy:
            expr: "slot('name_length')"
""",
    )

    scaffold["expected"]["name_length"] = 11
    scaffold["expected"]["name_length_copy"] = 11


@add_to_test_setup
def setup_hidden_slot(scaffold):
    """Hidden slot suppressed from output but available via slot()."""
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        slots:
          - greeting
    slots:
      greeting:
        range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          _hidden_name:
            hide: true
            expr: "{name}"
          greeting:
            expr: "'Hello, ' + slot('_hidden_name') + '!'"
""",
    )

    # _hidden_name should NOT appear in output
    scaffold["expected"]["greeting"] = "Hello, alice adams!"


@add_to_test_setup
def setup_hidden_slot_with_value_mappings(scaffold):
    """Hidden slot using value_mappings, referenced via slot()."""
    apply_schema_patch(
        scaffold["source_schema"],
        """
    classes:
      Person:
        slots:
          - status_code
    slots:
      status_code:
        range: string
""",
    )
    scaffold["input_data"]["status_code"] = "A"

    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        slots:
          - status_label
    slots:
      status_label:
        range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          _status:
            hide: true
            populated_from: status_code
            value_mappings:
              A: Active
              I: Inactive
          status_label:
            expr: "'Status: ' + slot('_status')"
""",
    )

    scaffold["expected"]["status_label"] = "Status: Active"


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


def test_hidden_slots_excluded_from_output(scaffold):
    """Hidden slots must not appear in output keys."""
    setup_hidden_slot(scaffold)
    result = run_transformer(scaffold)
    assert "_hidden_name" not in result
    assert "greeting" in result


def test_hidden_slot_with_value_mappings_excluded(scaffold):
    """Hidden slot with value_mappings must not appear in output keys."""
    setup_hidden_slot_with_value_mappings(scaffold)
    result = run_transformer(scaffold)
    assert "_status" not in result
    assert "status_label" in result


def test_slot_fn_returns_none_for_missing(scaffold):
    """slot() returns None for a slot name that doesn't exist."""
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        slots:
          - missing_ref
    slots:
      missing_ref:
        range: string
""",
    )
    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          missing_ref:
            expr: "slot('nonexistent')"
""",
    )
    result = run_transformer(scaffold)
    assert result["missing_ref"] is None


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
