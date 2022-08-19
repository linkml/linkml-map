import logging
import os
import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader
from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.transformer.object_transformer import ObjectTransformer

import tests.model.personinfo_s1 as src_dm
import tests.model.personinfo_s2 as tgt_dm

from tests import INPUT_DIR, SCHEMA1, SCHEMA2, SPECIFICATION


class TransformerTestCase(unittest.TestCase):

    def setUp(self) -> None:
        tr = ObjectTransformer()
        tr.source_schemaview = SchemaView(SCHEMA1)
        tr.target_schemaview = SchemaView(SCHEMA2)
        tr.target_module = tgt_dm
        tr.specification = yaml_loader.load(SPECIFICATION, target_class=TransformationSpecification)
        self.tr = tr

    def test_transform(self):
        """ tr """
        tr = self.tr
        obj = yaml_loader.load(str(INPUT_DIR / 'personinfo-s1-example-data-01.yaml'), target_class=src_dm.Person)
        target_obj = tr.transform(obj, target_class=tgt_dm.Agent)
        print(yaml_dumper.dumps(target_obj))
        #self.assertEqual(obj.name, target_obj.label)


if __name__ == '__main__':
    unittest.main()
