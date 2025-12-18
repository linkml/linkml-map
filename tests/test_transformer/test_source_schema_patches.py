"""Tests for source_schema_patches feature.

This feature allows augmenting auto-generated schemas with FK relationships
directly in the transform spec, enabling cross-class lookups without
modifying the source schema files.

Note: Uses standalone tests rather than shared scaffolds because this tests
an intentionally incomplete schema (no FK relationships) being patched.
"""

from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer


def test_source_schema_patches_enables_fk_lookup():
    """Patches add FK relationship to auto-generated schema, enabling cross-class lookup."""
    source_schema = SchemaView("""
id: https://example.org/autogen
name: autogen
classes:
  Container:
    tree_root: true
    attributes:
      persons:
        range: Person
        multivalued: true
        inlined_as_list: true
      organizations:
        range: Organization
        multivalued: true
        inlined_as_list: true
  Person:
    attributes:
      id:
        identifier: true
      name:
      org_id:
        range: string
  Organization:
    attributes:
      id:
        identifier: true
      name:
""")

    target_schema = SchemaView("""
id: https://example.org/target
name: target
classes:
  FlatPerson:
    attributes:
      id:
      name:
      org_name:
""")

    input_data = {
        "persons": [{"id": "P001", "name": "Alice", "org_id": "ORG001"}],
        "organizations": [{"id": "ORG001", "name": "Acme Corp"}],
    }

    transform_spec = {
        "source_schema_patches": {
            "classes": {
                "Person": {
                    "attributes": {
                        "org_id": {"range": "Organization"}
                    }
                }
            }
        },
        "class_derivations": {
            "FlatPerson": {
                "populated_from": "Person",
                "slot_derivations": {
                    "id": {},
                    "name": {},
                    "org_name": {"populated_from": "org_id.name"},
                },
            }
        },
    }

    obj_tr = ObjectTransformer(unrestricted_eval=False)
    obj_tr.source_schemaview = source_schema
    obj_tr.target_schemaview = target_schema
    obj_tr.create_transformer_specification(transform_spec)
    obj_tr.index(input_data, "Container")

    result = obj_tr.map_object(input_data["persons"][0], source_type="Person")

    assert result["id"] == "P001"
    assert result["name"] == "Alice"
    assert result["org_name"] == "Acme Corp"


def test_transform_works_without_patches():
    """Basic transform works when source_schema_patches is not provided."""
    source_schema = SchemaView("""
id: https://example.org/source
name: source
classes:
  Person:
    attributes:
      id:
        identifier: true
      name:
""")

    target_schema = SchemaView("""
id: https://example.org/target
name: target
classes:
  Agent:
    attributes:
      id:
      name:
""")

    transform_spec = {
        "class_derivations": {
            "Agent": {
                "populated_from": "Person",
                "slot_derivations": {
                    "id": {},
                    "name": {},
                },
            }
        },
    }

    obj_tr = ObjectTransformer(unrestricted_eval=False)
    obj_tr.source_schemaview = source_schema
    obj_tr.target_schemaview = target_schema
    obj_tr.create_transformer_specification(transform_spec)

    result = obj_tr.map_object({"id": "P001", "name": "Alice"}, source_type="Person")

    assert result["id"] == "P001"
    assert result["name"] == "Alice"
