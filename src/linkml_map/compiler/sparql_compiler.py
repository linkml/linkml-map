from linkml_map.compiler.compiler import CompiledSpecification, Compiler
from linkml_map.datamodel.transformer_model import TransformationSpecification


class SPARQLCompiler(Compiler):
    """
    Compiles a Transformation Specification to SPARQL Construct.

    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
