from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.datamodel.transformer_model import TransformationSpecification


class SSSOMCompiler(Compiler):
    """
    Compiles a Transformation Specification to SSSOM.

    Note: SSSOM has less expressivity so this is expected to be highly lossy
    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
