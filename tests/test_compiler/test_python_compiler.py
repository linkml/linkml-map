import unittest

from linkml_runtime import SchemaView

from linkml_transformer.compiler.python_compiler import PythonCompiler
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
