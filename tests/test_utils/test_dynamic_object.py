"""Test dynamic objects."""

import yaml
from linkml_runtime import SchemaView

from linkml_map.utils.dynamic_object import dynamic_object
from tests import FLATTENING_DATA, NORM_SCHEMA


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
