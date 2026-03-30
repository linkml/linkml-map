"""Regression test: scalar slots with no explicit range should not emit warnings.

When a source slot has no range (and no default_range), _map_value_by_range
should short-circuit for scalar and multivalued scalar values instead of
falling through to map_object, which would log "Unexpected: <value>" warnings.

See: https://github.com/linkml/linkml-map/pull/173
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

    classes:
      Record:
        attributes:
          id:
            identifier: true
          tag: {}
          tags:
            multivalued: true
""")

TARGET_SCHEMA = textwrap.dedent("""\
    id: https://example.org/target
    name: target
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types

    classes:
      Output:
        attributes:
          id: {}
          tag: {}
          tags:
            multivalued: true
""")


def _make_transformer() -> ObjectTransformer:
    """Build a transformer with schemas that have slots without explicit ranges."""
    transform = {
        "source_schema": "https://example.org/source",
        "target_schema": "https://example.org/target",
        "class_derivations": {
            "Output": {
                "populated_from": "Record",
                "slot_derivations": {
                    "id": {"populated_from": "id"},
                    "tag": {"populated_from": "tag"},
                    "tags": {"populated_from": "tags"},
                },
            }
        },
    }
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(transform)
    return tr


def test_scalar_no_range_no_warning(caplog):
    """Mapping a scalar slot with no range should not emit an 'Unexpected' warning."""
    tr = _make_transformer()
    result = tr.map_object({"id": "r1", "tag": "important"}, "Record")

    assert result["tag"] == "important"
    assert "Unexpected" not in caplog.text


def test_multivalued_scalar_no_range_no_warning(caplog):
    """Mapping a multivalued scalar slot with no range should not emit an 'Unexpected' warning."""
    tr = _make_transformer()
    result = tr.map_object({"id": "r1", "tags": ["a", "b", "c"]}, "Record")

    assert result["tags"] == ["a", "b", "c"]
    assert "Unexpected" not in caplog.text
