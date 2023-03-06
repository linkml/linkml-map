from linkml_runtime.utils.yamlutils import YAMLRoot

from linkml_transformer.compiler.compiler import Compiler
from linkml_transformer.datamodel.transformer_model import \
    TransformationSpecification


class SQLCompiler(Compiler):
    """
    Compiles a Transformation Specification to SQL CREATE TABLE or VIEW statements.

    """

    def compile(self, specification: TransformationSpecification) -> YAMLRoot:
        raise NotImplementedError
