from dataclasses import dataclass

from linkml_transformer.compiler.compiler import CompiledSpecification, Compiler
from linkml_transformer.compiler.j2_based_compiler import J2BasedCompiler
from linkml_transformer.datamodel.transformer_model import TransformationSpecification


@dataclass
class MarkdownCompiler(J2BasedCompiler):
    """
    Compiles a Transformation Specification to Markdown.
    """

    template_name: str = "markdown.j2"

