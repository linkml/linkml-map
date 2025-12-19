"""Tests for FK path resolution utilities."""

import pytest
from linkml_runtime import SchemaView

from linkml_map.utils.fk_utils import resolve_fk_path


@pytest.fixture
def schema_with_fk():
    """Schema with Person -> Organization FK relationship."""
    return SchemaView("""
id: https://example.org/test
name: test
classes:
  Person:
    attributes:
      id:
        identifier: true
      name:
      org_id:
        range: Organization
  Organization:
    attributes:
      id:
        identifier: true
      name:
      address:
        range: Address
  Address:
    attributes:
      city:
      country:
""")


def test_resolve_fk_path_simple(schema_with_fk):
    """Resolve single-level FK path like org_id.name."""
    result = resolve_fk_path(schema_with_fk, "Person", "org_id.name")

    assert result is not None
    assert result.fk_slot_name == "org_id"
    assert result.target_class == "Organization"
    assert result.remaining_path == "name"
    assert result.final_slot is not None
    assert result.final_slot.name == "name"


def test_resolve_fk_path_nested(schema_with_fk):
    """Resolve multi-level FK path like org_id.address.city."""
    result = resolve_fk_path(schema_with_fk, "Person", "org_id.address.city")

    assert result is not None
    assert result.fk_slot_name == "org_id"
    assert result.target_class == "Organization"
    assert result.remaining_path == "address.city"
    assert result.final_slot is not None
    assert result.final_slot.name == "city"


def test_resolve_fk_path_no_dot(schema_with_fk):
    """Non-FK path (no dot) returns None."""
    result = resolve_fk_path(schema_with_fk, "Person", "name")

    assert result is None


def test_resolve_fk_path_invalid_slot(schema_with_fk):
    """Invalid FK slot returns None."""
    result = resolve_fk_path(schema_with_fk, "Person", "nonexistent.name")

    assert result is None


def test_resolve_fk_path_non_class_range(schema_with_fk):
    """FK slot with non-class range returns None."""
    result = resolve_fk_path(schema_with_fk, "Person", "name.something")

    assert result is None
