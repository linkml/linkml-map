from linkml_runtime.utils.yamlutils import YAMLRoot

from linkml_transformer.compiler.compiler import Compiler
from linkml_transformer.datamodel.transformer_model import \
    TransformationSpecification


class SSSOMCompiler(Compiler):
    """
    Compiles a Transformation Specification to SSSOM.

    Note: SSSOM has less expressivity so this is expected to be highly lossy
    """

    def compile(self, specification: TransformationSpecification) -> YAMLRoot:
        raise NotImplementedError
