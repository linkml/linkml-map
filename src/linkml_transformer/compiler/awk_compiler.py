from linkml_runtime.utils.yamlutils import YAMLRoot

from linkml_transformer.compiler.compiler import Compiler
from linkml_transformer.datamodel.transformer_model import \
    TransformationSpecification


class AWKCompiler(Compiler):
    """
    Compiles a Transformation Specification to an Awk script.

    Note: this is only expected to work for flat schemas.
    """

    def compile(self, specification: TransformationSpecification) -> YAMLRoot:
        raise NotImplementedError
