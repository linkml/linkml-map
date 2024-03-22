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
from linkml_transformer.utils.loaders import load_specification
from tests import SCHEMA1, SPECIFICATION


@pytest.fixture
def session():
    session = Session()
    session.set_source_schema(SCHEMA1)
    session.set_transformer_specification(SPECIFICATION)
    return session


def test_compile(session):
    compiler = SQLCompiler()
    assert session.transformer_specification is not None
    compiled = compiler.compile(session.transformer_specification)
    # TODO: include imports so that code compiles
    print(compiled.serialization)
    source_sv = SchemaView(SCHEMA1)
    source_ddl = compiler.create_ddl(source_sv)
    print(source_ddl)
    target_sv = session.target_schemaview
    print(yaml_dumper.dumps(target_sv.schema))
    target_ddl = compiler.create_ddl(target_sv)
    print(target_ddl)


    import duckdb
    conn = duckdb.connect(':memory:')
    conn.execute(target_ddl)
    conn.execute(compiled.serialization)
