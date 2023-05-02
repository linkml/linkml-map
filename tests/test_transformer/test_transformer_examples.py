import unittest

import yaml

from linkml_transformer.transformer.object_transformer import ObjectTransformer
from tests import EXAMPLE_DIR

EXAMPLES = [
    ("measurements", "quantity_value", "qv-to-scalar", "PersonQuantityValue-001", 172.0),
    ("measurements", "quantity_value", "qv-to-scalar", "PersonQuantityValue-002", None),
]


class TransformerExamplesTestCase(unittest.TestCase):
    """
    Tests ObjectTransformer using examples
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
            tr.load_transformer_specification(path / "transform" / f"{spec}.transform.yaml")
            input_obj = yaml.safe_load(open(str(path / "data" / f"{data}.yaml")))
            target_obj = tr.transform(input_obj)
            self.assertEqual(expected, target_obj["height_in_cm"])
