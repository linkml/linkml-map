"""Test dynamic objects."""

import yaml
from linkml_runtime import SchemaView

from linkml_map.utils.dynamic_object import dynamic_object
from tests import FLATTENING_DATA, NORM_SCHEMA

NO_ID_SCHEMA = """
id: https://example.org/no-id
name: no_id
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types

classes:
  Container:
    attributes:
      items:
        range: Item
        multivalued: true
        inlined_as_list: false
  Item:
    attributes:
      value:
        range: string
"""

KEY_BASED_SCHEMA = """
id: https://example.org/key-based
name: key_based
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types

classes:
  Container:
    attributes:
      items:
        range: Item
        multivalued: true
        inlined_as_list: false
  Item:
    attributes:
      name:
        key: true
      value:
        range: string
"""


def test_dynamic_object() -> None:
    """Basic test for generating a dynamic object."""
    sv = SchemaView(NORM_SCHEMA)
    container = yaml.safe_load(open(str(FLATTENING_DATA)))
    dynobj = dynamic_object(container, sv, "MappingSet")
    assert type(dynobj).__name__ == "MappingSet"
    assert type(dynobj.entities["X:1"]).__name__ == "Entity"
    assert isinstance(dynobj.entities, dict)
    m = dynobj.mappings[0]
    assert type(m).__name__ == "Mapping"


def test_dynamic_object_key_based_class() -> None:
    """Test that dynamic_object handles classes with key: true (not identifier: true)."""
    sv = SchemaView(KEY_BASED_SCHEMA)
    data = {"items": {"alpha": {"value": "one"}, "beta": {"value": "two"}}}
    dynobj = dynamic_object(data, sv, "Container")
    assert type(dynobj).__name__ == "Container"
    assert isinstance(dynobj.items, dict)
    assert type(dynobj.items["alpha"]).__name__ == "Item"
    assert dynobj.items["alpha"].name == "alpha"
    assert dynobj.items["alpha"].value == "one"
    assert dynobj.items["beta"].name == "beta"


def test_dynamic_object_no_identifier_or_key() -> None:
    """Test that dynamic_object handles dict-inlined classes with no identifier or key."""
    sv = SchemaView(NO_ID_SCHEMA)
    data = {"items": {"x": {"value": "one"}, "y": {"value": "two"}}}
    dynobj = dynamic_object(data, sv, "Container")
    assert type(dynobj).__name__ == "Container"
    assert isinstance(dynobj.items, dict)
    assert dynobj.items["x"].value == "one"
