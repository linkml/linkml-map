from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.datamodel.transformer_model import TransformationSpecification


class AWKCompiler(Compiler):
    """
    Compiles a Transformation Specification to an Awk script.

    Note: this is only expected to work for flat schemas.
    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
