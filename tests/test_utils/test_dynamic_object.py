import unittest

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.loaders import yaml_loader

from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.transformer.object_transformer import ObjectTransformer
from linkml_transformer.utils.dynamic_object import dynamic_object
from tests import (DENORM_SCHEMA, DENORM_SPECIFICATION, FLATTENING_DATA,
                   NORM_SCHEMA, PERSONINFO_DATA, PERSONINFO_SRC_SCHEMA,
                   PERSONINFO_TGT_SCHEMA, PERSONINFO_TR)


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
