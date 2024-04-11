import unittest

import yaml
from linkml_runtime import SchemaView

from linkml_map.utils.dynamic_object import dynamic_object
from tests import FLATTENING_DATA, NORM_SCHEMA


class DynamicObjectTestCase(unittest.TestCase):
    """
    Tests Dynamic Objects
    """

    def test_dynamic_object(self):
        sv = SchemaView(NORM_SCHEMA)
        container = yaml.safe_load(open(str(FLATTENING_DATA)))
        dynobj = dynamic_object(container, sv, "MappingSet")
        self.assertEqual("MappingSet", type(dynobj).__name__)
        self.assertEqual("Entity", type(dynobj.entities["X:1"]).__name__)
        self.assertIsInstance(dynobj.entities, dict)
        m = dynobj.mappings[0]
        self.assertEqual("Mapping", type(m).__name__)
        # container["mappings"][0].subject = "U:1"
        # dynobj = dynamic_object(container, sv, "MappingSet")


if __name__ == "__main__":
    unittest.main()
