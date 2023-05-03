from linkml_transformer.compiler.compiler import CompiledSpecification, Compiler
from linkml_transformer.datamodel.transformer_model import TransformationSpecification


class SQLCompiler(Compiler):
    """
    Compiles a Transformation Specification to SQL CREATE TABLE or VIEW statements.

    """

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        raise NotImplementedError
