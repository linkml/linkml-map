import unittest

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader

from linkml_transformer.datamodel.transformer_model import TransformationSpecification
from linkml_transformer.transformer.object_transformer import ObjectTransformer
from tests import PERSONINFO_TR


class DatamodelTestCase(unittest.TestCase):
    """
    tests the data model
    """

    def setUp(self) -> None:
        tr = ObjectTransformer()
        tr.load_transformer_specification(PERSONINFO_TR)
        self.tr_spec = tr.specification

    def test_datamodel(self):
        """checks loading/retrieval"""
        tr_spec = self.tr_spec
        # print(tr_spec.json())
        self.assertNotEqual("", tr_spec.json())


if __name__ == "__main__":
    unittest.main()
