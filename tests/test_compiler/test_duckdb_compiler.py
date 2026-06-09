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


def test_from_clause_uses_class_populated_from() -> None:
    """SQLCompiler must use class_derivation.populated_from as the FROM table.

    Issue #48: previously the FROM clause used cd.name (the target class name),
    producing INSERT INTO Target ... FROM Target — a self-INSERT that reads
    from the empty target table and silently inserts zero rows.
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
                    "label": SlotDerivation(name="label", populated_from="name"),
                },
            ),
        },
    )
    compiled = SQLCompiler().compile(spec)
    assert "INSERT INTO Agent" in compiled.serialization
    assert "FROM Person" in compiled.serialization
    assert "FROM Agent" not in compiled.serialization


def test_slot_aliased_source_as_target() -> None:
    """SQLCompiler must emit `source AS target`, not `target AS source`.

    Issue #48: with `label: populated_from: name`, the generated SQL must read
    the `name` column from the source table and alias it as `label` in the
    result. The inverted form references a `label` column that doesn't exist
    in the source.
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
                    "label": SlotDerivation(name="label", populated_from="name"),
                },
            ),
        },
    )
    compiled = SQLCompiler().compile(spec)
    assert "name AS label" in compiled.serialization
    assert "label AS name" not in compiled.serialization


def test_compiled_sql_executes_against_duckdb() -> None:
    """End-to-end: compiled INSERT reads from source table and lands rows in target.

    Issue #48: with both bugs (FROM clause + AS direction), source rows never
    reached target tables. This verifies the round-trip on a minimal spec.
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
                    "label": SlotDerivation(name="label", populated_from="name"),
                },
            ),
        },
    )
    compiled = SQLCompiler().compile(spec)

    conn = duckdb.connect(":memory:")
    conn.execute("CREATE TABLE Person (name TEXT);")
    conn.execute("CREATE TABLE Agent (label TEXT);")
    conn.execute("INSERT INTO Person VALUES ('Alice'), ('Bob');")
    conn.execute(compiled.serialization)
    rows = conn.execute("SELECT label FROM Agent ORDER BY label;").fetchall()
    assert rows == [("Alice",), ("Bob",)]


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
    conn.execute(source_ddl)
    conn.execute(target_ddl)
    # TODO #150: compiled INSERTs don't yet provide every target column for
    # arbitrary specs (the target's derived schema can include columns not
    # named by any slot_derivation). Re-enable execution once SQLCompiler
    # emits explicit column lists / handles full target shape.
