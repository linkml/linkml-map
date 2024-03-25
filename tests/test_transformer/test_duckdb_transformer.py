"""
Tests compilation of a specification to python
"""

import pytest
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils.compile_python import compile_python

import tests.input.examples.personinfo_basic.model.personinfo_model as src
from linkml_transformer.compiler.sql_compiler import SQLCompiler
from linkml_transformer.session import Session
from linkml_transformer.transformer.duckdb_transformer import DuckDBTransformer
from linkml_transformer.utils.loaders import load_specification
from tests import (
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TGT_SCHEMA,
    PERSONINFO_TR,
    SCHEMA1,
    SPECIFICATION,
)


@pytest.fixture
def session() -> Session:
    session = Session()
    session.set_source_schema(PERSONINFO_SRC_SCHEMA)
    session.set_transformer_specification(PERSONINFO_TR)
    if not session.transformer_specification:
        raise ValueError("No specification provided.")
    tr = DuckDBTransformer()
    session.set_transformer(tr)
    tr.specification = session.transformer_specification
    tr.source_schemaview = SchemaView(str(PERSONINFO_SRC_SCHEMA))
    tr.target_schemaview = SchemaView(str(PERSONINFO_TGT_SCHEMA))
    return session


def test_compile(session: Session):
    pytest.skip("TODO")
    session.transformer.map_database(":memory:")
