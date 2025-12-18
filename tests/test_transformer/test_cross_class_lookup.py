"""Tests for cross-class slot lookup via FK relationships (Issue #97).

Uses the scaffold-based testing architecture where:
- Scaffold provides working setup with Person -> Organization FK
- Each @add_to_container_test_setup function adds one slot derivation to test
- Unit tests run each setup independently
- Integration test runs all setups cumulatively
"""

import logging
import pytest

from linkml_map.transformer.object_transformer import ObjectTransformer
from tests.conftest import add_to_container_test_setup, CONTAINER_TEST_SETUP_FUNCTIONS
from tests.scaffold.utils.apply_patch import apply_schema_patch, apply_transform_patch


def run_container_transformer(scaffold):
    """Run transformer with ObjectIndex for cross-class lookups."""
    obj_tr = ObjectTransformer(unrestricted_eval=False)
    obj_tr.source_schemaview = scaffold["source_schema"]
    obj_tr.target_schemaview = scaffold["target_schema"]
    obj_tr.create_transformer_specification(scaffold["transform_spec"])
    obj_tr.index(scaffold["input_data"], "Container")
    return obj_tr.map_object(scaffold["input_data"]["persons"][0], source_type="Person")


@add_to_container_test_setup
def setup_populated_from_fk_name(scaffold):
    """Populate slot from FK using populated_from dot notation."""
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      FlatPerson:
        attributes:
          org_name:
            range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      FlatPerson:
        slot_derivations:
          org_name:
            populated_from: org_id.name
""",
    )

    scaffold["expected"]["org_name"] = "Acme Corp"


@add_to_container_test_setup
def setup_populated_from_fk_city(scaffold):
    """Populate slot from different FK attribute (city)."""
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      FlatPerson:
        attributes:
          org_city:
            range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      FlatPerson:
        slot_derivations:
          org_city:
            populated_from: org_id.city
""",
    )

    scaffold["expected"]["org_city"] = "Springfield"


@add_to_container_test_setup
def setup_expr_fk_lookup(scaffold):
    """Expression with FK dereference (regression - already works)."""
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      FlatPerson:
        attributes:
          org_name_expr:
            range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      FlatPerson:
        slot_derivations:
          org_name_expr:
            expr: "org_id.name"
""",
    )

    scaffold["expected"]["org_name_expr"] = "Acme Corp"


@add_to_container_test_setup
def setup_missing_fk_reference(scaffold):
    """FK pointing to non-existent object returns None."""
    apply_schema_patch(
        scaffold["source_schema"],
        """
    classes:
      Person:
        attributes:
          missing_org_id:
            range: Organization
""",
    )

    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      FlatPerson:
        attributes:
          org_name_missing:
            range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      FlatPerson:
        slot_derivations:
          org_name_missing:
            populated_from: missing_org_id.name
""",
    )

    scaffold["input_data"]["persons"][0]["missing_org_id"] = "NONEXISTENT"
    scaffold["expected"]["org_name_missing"] = None


@add_to_container_test_setup
def setup_null_fk_value(scaffold):
    """Null FK value returns None."""
    apply_schema_patch(
        scaffold["source_schema"],
        """
    classes:
      Person:
        attributes:
          null_org_id:
            range: Organization
""",
    )

    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      FlatPerson:
        attributes:
          org_name_null:
            range: string
""",
    )

    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      FlatPerson:
        slot_derivations:
          org_name_null:
            populated_from: null_org_id.name
""",
    )

    scaffold["input_data"]["persons"][0]["null_org_id"] = None
    scaffold["expected"]["org_name_null"] = None


def test_basic_person_to_flat_person(container_scaffold):
    """Ensure basic scaffold works: Person -> FlatPerson with id and name."""
    result = run_container_transformer(container_scaffold)
    assert result == container_scaffold["expected"]


@pytest.mark.parametrize(
    "setup_func",
    CONTAINER_TEST_SETUP_FUNCTIONS,
    ids=[f.__doc__ or f.__name__ for f in CONTAINER_TEST_SETUP_FUNCTIONS],
)
def test_unit(container_scaffold, setup_func):
    """Unit test for each setup function."""
    setup_func(container_scaffold)
    result = run_container_transformer(container_scaffold)
    assert result == container_scaffold["expected"]


def test_integration(integration_container_scaffold):
    """Integration test: all setup functions applied cumulatively."""
    result = run_container_transformer(integration_container_scaffold)
    assert result == integration_container_scaffold["expected"]


def test_no_object_index_warning(container_scaffold, caplog):
    """Without object_index, cross-class lookup returns None with warning."""
    apply_schema_patch(
        container_scaffold["target_schema"],
        """
    classes:
      FlatPerson:
        attributes:
          org_name:
            range: string
""",
    )

    apply_transform_patch(
        container_scaffold["transform_spec"],
        """
    class_derivations:
      FlatPerson:
        slot_derivations:
          org_name:
            populated_from: org_id.name
""",
    )

    source = container_scaffold["source_schema"]
    target = container_scaffold["target_schema"]

    obj_tr = ObjectTransformer(unrestricted_eval=False)
    obj_tr.source_schemaview = source
    obj_tr.target_schemaview = target
    obj_tr.create_transformer_specification(container_scaffold["transform_spec"])
    # Intentionally skip index() to trigger warning

    with caplog.at_level(logging.WARNING):
        result = obj_tr.map_object(
            container_scaffold["input_data"]["persons"][0], source_type="Person"
        )

    assert result.get("org_name") is None
    assert "object_index" in caplog.text
