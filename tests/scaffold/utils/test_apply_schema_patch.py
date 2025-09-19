import pytest
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SchemaDefinition, Prefix, SlotDefinition, EnumDefinition, TypeDefinition

from tests.scaffold.utils.apply_patch import apply_schema_patch

@pytest.fixture
def empty_schemaview():
    return SchemaView(SchemaDefinition(id="http://example.org/schema", name="test_schema"))

def test_add_slot(empty_schemaview):
    apply_schema_patch(empty_schemaview, """
    slots:
      age:
        range: integer
    """)
    assert "age" in empty_schemaview.schema.slots
    assert empty_schemaview.schema.slots["age"].range == "integer"

def test_patch_existing_slot(empty_schemaview):
    empty_schemaview.schema.slots["age"] = SlotDefinition(name="age", range="integer")
    apply_schema_patch(empty_schemaview, """
    slots:
      age:
        description: "Age of the person"
    """)
    assert empty_schemaview.schema.slots["age"].description == "Age of the person"
    assert empty_schemaview.schema.slots["age"].range == "integer"  # unchanged

def test_add_class_with_slot(empty_schemaview):
    apply_schema_patch(empty_schemaview, """
    classes:
      Person:
        slots:
          - name
    slots:
      name:
        range: string
    """)
    assert "Person" in empty_schemaview.schema.classes
    assert "name" in empty_schemaview.schema.slots
    assert "name" in empty_schemaview.schema.classes["Person"].slots

def test_add_prefix_and_import(empty_schemaview):
    apply_schema_patch(empty_schemaview, """
    imports:
      - linkml:types
    prefixes:
      ex:
        prefix_reference: http://example.org/
    """)
    assert "linkml:types" in empty_schemaview.schema.imports
    assert "ex" in empty_schemaview.schema.prefixes
    assert empty_schemaview.schema.prefixes["ex"].prefix_reference == "http://example.org/"

def test_patch_top_level_fields(empty_schemaview):
    apply_schema_patch(empty_schemaview, """
    id: http://example.org/schema
    name: PatchedSchema
    description: "Patched schema for testing"
    default_prefix: ex
    """)
    assert empty_schemaview.schema.id == "http://example.org/schema"
    assert empty_schemaview.schema.name == "PatchedSchema"
    assert empty_schemaview.schema.description == "Patched schema for testing"
    assert empty_schemaview.schema.default_prefix == "ex"
