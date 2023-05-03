from linkml_transformer.compiler.compiler import CompiledSpecification, Compiler
from linkml_transformer.datamodel.transformer_model import TransformationSpecification


class AWKCompiler(Compiler):
    """
    Compiles a Transformation Specification to an Awk script.

    Note: this is only expected to work for flat schemas.
    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
