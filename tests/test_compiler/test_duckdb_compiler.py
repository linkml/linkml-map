"""
Tests compilation of a specification to python.
"""

import duckdb
import pytest
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper

from linkml_map.compiler.sql_compiler import SQLCompiler
from linkml_map.session import Session
from tests import SCHEMA1, SPECIFICATION


@pytest.fixture
def session() -> Session:
    """LinkML transformer session with schema and spec set."""
    session = Session()
    session.set_source_schema(SCHEMA1)
    session.set_transformer_specification(SPECIFICATION)
    return session


def test_compile(session: Session) -> None:
    """Test the DuckDb compiler."""
    compiler = SQLCompiler()
    assert session.transformer_specification is not None
    compiled = compiler.compile(session.transformer_specification)
    # TODO: include imports so that code compiles
    print("Compiled SQL:")
    print(compiled.serialization)
    source_sv = SchemaView(SCHEMA1)
    source_ddl = compiler.create_ddl(source_sv)
    print("Source DDL:")
    print(source_ddl)
    target_sv = session.target_schemaview
    print("Target Schema:")
    print(yaml_dumper.dumps(target_sv.schema))
    target_ddl = compiler.create_ddl(target_sv)
    print("Target DDL:")
    print(target_ddl)

    conn = duckdb.connect(":memory:")
    conn.execute(target_ddl)
    conn.execute(compiled.serialization)
