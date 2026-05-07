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


def test_hidden_slots_excluded_from_sql() -> None:
    """SQLCompiler must not emit columns for slot derivations with hide: true.

    Hidden slots are runtime-only intermediates for slot() references; emitting
    them as SQL columns would reference target columns that SchemaMapper does not
    materialize, producing broken SQL.
    """
    from linkml_map.datamodel.transformer_model import (
        ClassDerivation,
        SlotDerivation,
        TransformationSpecification,
    )

    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "Agent": ClassDerivation(
                name="Agent",
                populated_from="Person",
                slot_derivations={
                    "_intermediate": SlotDerivation(name="_intermediate", populated_from="name", hide=True),
                    "label": SlotDerivation(name="label", populated_from="name"),
                },
            ),
        },
    )
    compiler = SQLCompiler()
    compiled = compiler.compile(spec)
    assert "_intermediate" not in compiled.serialization
    assert "label" in compiled.serialization


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
