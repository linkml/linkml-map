from linkml_transformer.compiler.compiler import CompiledSpecification, Compiler
from linkml_transformer.datamodel.transformer_model import TransformationSpecification


class SPARQLCompiler(Compiler):
    """
    Compiles a Transformation Specification to SPARQL Construct.

    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
