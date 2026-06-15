"""Tests for inlined `populated_from` dot-path traversal (issue #247).

`populated_from` dot-paths walk FK joins via ObjectIndex; #247 extends them to
traverse *inlined* nested data (XML/JSON/OWL/EML-shaped trees) by walking into
the nested object structurally instead of treating it as a foreign key.

Scope of #247 (this file): slot-level traversal to a scalar leaf. Multivalued
inline fan-out (a list segment auto-firing a sibling class_derivation per item)
is tracked separately in #265 and here is asserted to raise a clear diagnostic.
"""

import pytest
from linkml_runtime import SchemaView

from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer

# Source: an EML-ish inlined tree. EMLDocument -> dataset (inlined) -> dataTable (inlined list).
SOURCE_SCHEMA = """\
id: https://example.org/eml-source
name: eml-source
prefixes:
  linkml: https://w3id.org/linkml/
default_range: string
imports:
  - linkml:types
classes:
  EMLDocument:
    tree_root: true
    attributes:
      dataset:
        range: Dataset
        inlined: true
  Dataset:
    attributes:
      title:
        range: string
      dataTable:
        range: DataTable
        multivalued: true
        inlined_as_list: true
  DataTable:
    attributes:
      entityName:
        range: string
"""

# Target: a flattened LinkML-metamodel-ish shape.
TARGET_SCHEMA = """\
id: https://example.org/schema-target
name: schema-target
prefixes:
  linkml: https://w3id.org/linkml/
default_range: string
imports:
  - linkml:types
classes:
  SchemaDefinition:
    tree_root: true
    attributes:
      title:
        range: string
      classes:
        range: ClassDefinition
        multivalued: true
        inlined_as_list: true
  ClassDefinition:
    attributes:
      name:
        range: string
"""

INPUT_DATA = {
    "dataset": {
        "title": "My Dataset",
        "dataTable": [
            {"entityName": "table_one"},
            {"entityName": "table_two"},
        ],
    },
}


def _make_transformer(transform_spec: dict, source_schema: str = SOURCE_SCHEMA) -> ObjectTransformer:
    tr = ObjectTransformer(unrestricted_eval=False)
    tr.source_schemaview = SchemaView(source_schema)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(transform_spec)
    return tr


def _title_spec() -> dict:
    return {
        "class_derivations": {
            "SchemaDefinition": {
                "populated_from": "EMLDocument",
                "slot_derivations": {
                    "title": {"populated_from": "dataset.title"},
                },
            },
        },
    }


def test_slot_level_inline_deep_scalar():
    """Dot-path into an inlined object reaches the scalar leaf without an ObjectIndex."""
    tr = _make_transformer(_title_spec())
    result = tr.map_object(INPUT_DATA, source_type="EMLDocument")
    assert result["title"] == "My Dataset"


def test_inline_path_via_runtime_fallback_without_inlined_declaration():
    """A dict value traverses even when the source schema omits ``inlined: true``."""
    source = SOURCE_SCHEMA.replace("        inlined: true\n", "")
    tr = _make_transformer(_title_spec(), source_schema=source)
    result = tr.map_object(INPUT_DATA, source_type="EMLDocument")
    assert result["title"] == "My Dataset"


def test_inline_path_absent_segment_yields_none():
    """A legitimately missing leaf yields None rather than raising."""
    tr = _make_transformer(_title_spec())
    result = tr.map_object({"dataset": {}}, source_type="EMLDocument")
    assert result.get("title") is None


def test_multivalued_inline_segment_raises_clear_diagnostic():
    """A list segment is the #265 fan-out case: raise naming the segment, not silent None."""
    spec = {
        "class_derivations": {
            "SchemaDefinition": {
                "populated_from": "EMLDocument",
                "slot_derivations": {
                    "classes": {"populated_from": "dataset.dataTable"},
                },
            },
        },
    }
    tr = _make_transformer(spec)
    with pytest.raises(TransformationError, match=r"dataTable.*#265"):
        tr.map_object(INPUT_DATA, source_type="EMLDocument")
