from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.datamodel.transformer_model import TransformationSpecification


class R2RMLCompiler(Compiler):
    """
    Compiles a Transformation Specification to R2RML.

    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
