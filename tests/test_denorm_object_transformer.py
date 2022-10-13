import logging
import os
import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader
from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.transformer.object_transformer import ObjectTransformer

import tests.model.mapping_norm as src_dm
import tests.model.mapping_denorm as tgt_dm

from tests import INPUT_DIR, SCHEMA1, SCHEMA2, SPECIFICATION, DENORM_SPECIFICATION, NORM_SCHEMA, DENORM_SCHEMA


class ObjectTransformerTestCase(unittest.TestCase):
    """
    Tests ObjectTransformer
    """

    def setUp(self) -> None:
        tr = ObjectTransformer()
        tr.source_schemaview = SchemaView(NORM_SCHEMA)
        tr.target_schemaview = SchemaView(DENORM_SCHEMA)
        tr.target_module = tgt_dm
        tr.specification = yaml_loader.load(DENORM_SPECIFICATION, target_class=TransformationSpecification)
        self.tr = tr


    def test_transform(self):
        """ tests recursive """
        tr = self.tr
        mset: src_dm.MappingSet = yaml_loader.load(str(INPUT_DIR / 'mappingset-norm-example-01.yaml'), target_class=src_dm.MappingSet)
        tr.index(mset)
        target_obj: tgt_dm.MappingSet = tr.transform(mset, target_class=tgt_dm.MappingSet)
        print(yaml_dumper.dumps(target_obj))





if __name__ == '__main__':
    unittest.main()
