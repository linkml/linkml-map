import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader

from linkml_transformer.compiler.python_compiler import PythonCompiler
from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.schema_mapper.schema_mapper import SchemaMapper
from linkml_transformer.transformer.object_transformer import ObjectTransformer
from linkml_transformer.utils.loaders import load_specification
from tests import SCHEMA1, SPECIFICATION


class PythonCompilerTestCase(unittest.TestCase):
    """
    Tests compilation of a specification to python
    """

    def setUp(self) -> None:
        self.compiler = PythonCompiler(source_schemaview=SchemaView(SCHEMA1))

    def test_compile(self):
        spec = load_specification(SPECIFICATION)
        pycode = self.compiler.compile(spec)
        print(pycode.serialization)




if __name__ == "__main__":
    unittest.main()
