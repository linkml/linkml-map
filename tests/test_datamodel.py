import logging
import os
import unittest

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader

from linkml_transformer.datamodel.transformer_model import *
from tests import PERSONINFO_TR


class DatamodelTestCase(unittest.TestCase):
    """
    tests the data model
    """

    def setUp(self) -> None:
        self.tr_spec = yaml_loader.load(
            str(PERSONINFO_TR), target_class=TransformationSpecification
        )

    def test_datamodel(self):
        """checks loading/retrieval"""
        tr_spec = self.tr_spec
        print(yaml_dumper.dumps(tr_spec))
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
