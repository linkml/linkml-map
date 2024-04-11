"""
Tests compilation of a specification to graphviz
"""

import pytest
from linkml_runtime import SchemaView

from linkml_map.compiler.graphviz_compiler import GraphvizCompiler
from linkml_map.utils.loaders import load_specification
from tests import OUTPUT_DIR, SCHEMA1, SPECIFICATION


@pytest.fixture
def compiler():
    return GraphvizCompiler(
        source_schemaview=SchemaView(SCHEMA1),
    )


def test_compile(compiler):
    spec = load_specification(SPECIFICATION)
    compiled = compiler.compile(spec)
    # print(compiled.serialization)
    assert (
        "sourceMapping:id -> targetDenormMapping:subject_id [style=dashed]"
        in compiled.serialization
    )
    compiled.render(OUTPUT_DIR / "test.png", view=False)
