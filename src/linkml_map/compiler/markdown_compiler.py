from dataclasses import dataclass

from linkml_map.compiler.j2_based_compiler import J2BasedCompiler


@dataclass
class MarkdownCompiler(J2BasedCompiler):
    """
    Compiles a Transformation Specification to Markdown.
    """

    template_name: str = "markdown.j2"
