import unittest

import yaml

from linkml_transformer.transformer.object_transformer import ObjectTransformer
from linkml_transformer.utils.dynamic_object import dynamic_object
from linkml_transformer.utils.multi_file_transformer import MultiFileTransformer
from tests import EXAMPLE_DIR

EXAMPLES = [
    ("measurements", "quantity_value", "qv-to-scalar", "PersonQuantityValue-001", 172.0),
    ("measurements", "quantity_value", "qv-to-scalar", "PersonQuantityValue-002", None),
]


class TransformerExamplesTestCase(unittest.TestCase):
    """
    Tests ObjectTransformer using examples.

    Assumes folder structures:

    - input/examples
       - {package}
          - source/{source_schema}.yaml  :: the schema to transform from
          - transform/{transform_spec}.transform.yaml :: mapping spec
          - data/{SourceClassName}-{LocalId}.yaml :: data to transform
          - target/{SourceClassName}-{LocalId}.yaml :: expected output data
    """

    def test_examples(self):
        """
        Tests transforming a Person object from s1 to an Agent object in s2
        """
        for example in EXAMPLES:
            folder, src, spec, data, expected = example
            path = EXAMPLE_DIR / folder
            tr = ObjectTransformer()
            tr.load_source_schema(path / "source" / f"{src}.yaml")
            tr.load_transformer_specification(
                path / "transform" / f"{spec}.transform.yaml"
            )
            input_obj = yaml.safe_load(open(str(path / "data" / f"{data}.yaml")))
            target_obj = tr.transform(input_obj)
            # target_obj = dynamic_object(target_obj, "Person")
            self.assertEqual(expected, target_obj["height_in_cm"])

    def test_all(self):
        """
        Iterates through all examples
        :return:
        """
        mft = MultiFileTransformer()
        dirs = ["measurements"]
        for dir in dirs:
            full_dir = EXAMPLE_DIR / dir
            instructions = mft.infer_instructions(full_dir)
            print(instructions)
            obj = mft.process_instructions(instructions, full_dir)
            print(obj)

