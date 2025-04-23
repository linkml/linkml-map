"""
Tests compilation of a specification to markdown.
"""

import pytest
from linkml_runtime import SchemaView

from linkml_map.compiler.markdown_compiler import MarkdownCompiler
from linkml_map.utils.loaders import load_specification
from tests import SCHEMA1, SPECIFICATION


@pytest.fixture
def compiler() -> MarkdownCompiler:
    """Instantiate a MarkdownCompiler."""
    return MarkdownCompiler(
        source_schemaview=SchemaView(SCHEMA1),
    )


def test_compile(compiler: MarkdownCompiler) -> None:
    """Basic test of Markdown Compiler functioning."""
    assert compiler.template_name is not None
    spec = load_specification(SPECIFICATION)
    markdown = compiler.compile(spec).serialization
    print(markdown)
