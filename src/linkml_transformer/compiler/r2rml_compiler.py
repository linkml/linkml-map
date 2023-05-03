from linkml_transformer.compiler.compiler import CompiledSpecification, Compiler
from linkml_transformer.datamodel.transformer_model import TransformationSpecification


class R2RMLCompiler(Compiler):
    """
    Compiles a Transformation Specification to R2RML.

    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
