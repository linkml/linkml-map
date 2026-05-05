"""Regression test for expr with spaces in source class names.

When the source class name contains a space (e.g. "my record"), expr-based
slot derivations should still be able to access source object fields.

See: https://github.com/linkml/linkml-map/issues/170
"""

import textwrap

from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/source
    name: source
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string

    classes:
      my record:
        attributes:
          record_id:
            identifier: true
          label: {}
          source_ref: {}
""")

TARGET_SCHEMA = textwrap.dedent("""\
    id: https://example.org/target
    name: target
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string

    classes:
      Output:
        attributes:
          id: {}
          name: {}
          source: {}
""")

INPUT_OBJ = {
    "record_id": "rec-001",
    "label": "Hello World",
    "source_ref": "db:12345",
}


def _make_transformer(transform_spec: dict) -> ObjectTransformer:
    """Build an ObjectTransformer from inline schemas and a transform dict."""
    transform_spec["source_schema"] = "https://example.org/source"
    transform_spec["target_schema"] = "https://example.org/target"
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(transform_spec)
    return tr


def test_expr_with_space_in_class_name_no_index():
    """expr should resolve source fields when class name has a space (no index)."""
    transform = {
        "class_derivations": {
            "Output": {
                "populated_from": "my record",
                "slot_derivations": {
                    "id": {"populated_from": "record_id"},
                    "name": {"expr": "label"},
                    "source": {"expr": "source_ref"},
                },
            }
        },
    }
    tr = _make_transformer(transform)
    result = tr.map_object(INPUT_OBJ, "my record")

    assert result["id"] == "rec-001"
    assert result["name"] == "Hello World"
    assert result["source"] == "db:12345"


def test_expr_with_space_in_class_name_with_index():
    """expr should resolve source fields when class name has a space (with index)."""
    transform = {
        "class_derivations": {
            "Output": {
                "populated_from": "my record",
                "slot_derivations": {
                    "id": {"populated_from": "record_id"},
                    "name": {"expr": "label"},
                    "source": {"expr": "source_ref"},
                },
            }
        },
    }
    tr = _make_transformer(transform)
    tr.index(INPUT_OBJ, "my record")
    result = tr.map_object(INPUT_OBJ, "my record")

    assert result["id"] == "rec-001"
    assert result["name"] == "Hello World"
    assert result["source"] == "db:12345"


def test_expr_string_concat_with_space_in_class_name():
    """expr with string operations should work when class name has a space."""
    transform = {
        "class_derivations": {
            "Output": {
                "populated_from": "my record",
                "slot_derivations": {
                    "id": {"populated_from": "record_id"},
                    "name": {"expr": "label + ' (copy)'"},
                    "source": {"expr": "source_ref"},
                },
            }
        },
    }
    tr = _make_transformer(transform)
    result = tr.map_object(INPUT_OBJ, "my record")

    assert result["name"] == "Hello World (copy)"
