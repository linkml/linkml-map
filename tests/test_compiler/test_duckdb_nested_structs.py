"""
Tests that nested class_derivations compile to DuckDB STRUCTs rather than being dropped.

Covers the four nesting shapes called out in issue #151: a single nested object read from
the parent's own row, two-level nesting, a multivalued nested object read across a join, and
a multivalued nested object that is empty for most parent rows.
"""

import duckdb
import pytest
from linkml_runtime import SchemaView

from linkml_map.compiler.sql_compiler import SQLCompiler
from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    SlotDerivation,
    TransformationSpecification,
)

SOURCE_SCHEMA = """
id: https://example.org/src
name: src
prefixes:
  linkml: https://w3id.org/linkml/
default_range: string
imports:
  - linkml:types
classes:
  meas:
    attributes:
      meas_id:
        identifier: true
      set_id:
      assay_id:
      meas_value:
        range: float
      meas_unit:
  obs_set:
    attributes:
      set_id:
        identifier: true
  assay_tbl:
    attributes:
      assay_id:
        identifier: true
      assay_name:
      lower_value:
        range: float
      lower_unit:
      upper_value:
        range: float
      upper_unit:
  person_tbl:
    attributes:
      person_id:
        identifier: true
  death_tbl:
    attributes:
      d_person_id:
      cause:
"""

TARGET_SCHEMA = """
id: https://example.org/tgt
name: tgt
prefixes:
  linkml: https://w3id.org/linkml/
default_range: string
imports:
  - linkml:types
classes:
  Quantity:
    attributes:
      value:
        range: float
      unit:
  Assay:
    attributes:
      id:
        identifier: true
      name:
      lower_limit_of_detection:
        range: Quantity
        inlined: true
      upper_limit_of_detection:
        range: Quantity
        inlined: true
  MeasurementObservation:
    attributes:
      id:
        identifier: true
      value_quantity:
        range: Quantity
        inlined: true
      associated_assay:
        range: Assay
        inlined: true
  MeasurementObservationSet:
    attributes:
      id:
        identifier: true
      observations:
        range: MeasurementObservation
        multivalued: true
        inlined: true
        inlined_as_list: true
  CauseOfDeath:
    attributes:
      cause:
  Person:
    attributes:
      id:
        identifier: true
      cause_of_death:
        range: CauseOfDeath
        multivalued: true
        inlined: true
        inlined_as_list: true
"""


def _quantity_derivation(name: str, source: str, value_col: str, unit_col: str) -> ClassDerivation:
    """Build a Quantity derivation reading *value_col* / *unit_col* from *source*."""
    return ClassDerivation(
        name=name,
        populated_from=source,
        slot_derivations={
            "value": SlotDerivation(name="value", populated_from=value_col),
            "unit": SlotDerivation(name="unit", populated_from=unit_col),
        },
    )


@pytest.fixture
def source_schemaview() -> SchemaView:
    """View over the flat relational source schema."""
    return SchemaView(SOURCE_SCHEMA)


@pytest.fixture
def target_schemaview() -> SchemaView:
    """View over the nested target schema."""
    return SchemaView(TARGET_SCHEMA)


@pytest.fixture
def compiler(source_schemaview: SchemaView, target_schemaview: SchemaView) -> SQLCompiler:
    """SQLCompiler wired to both schemas, as DuckDBTransformer wires it."""
    return SQLCompiler(source_schemaview=source_schemaview, target_schemaview=target_schemaview)


@pytest.fixture
def connection(compiler: SQLCompiler, source_schemaview: SchemaView, target_schemaview: SchemaView):
    """In-memory DuckDB holding source and target tables, with source rows loaded."""
    con = duckdb.connect(":memory:")
    con.execute(compiler.create_ddl(source_schemaview))
    con.execute(compiler.create_ddl(target_schemaview))
    con.execute("INSERT INTO obs_set VALUES ('s1'), ('s2');")
    con.execute("INSERT INTO assay_tbl VALUES ('a1', 'glucose panel', 0.5, 'mg/dL', 500.0, 'mg/dL');")
    con.execute("INSERT INTO meas VALUES ('m1', 's1', 'a1', 1.5, 'mg/dL'), ('m2', 's1', 'a1', 2.5, 'mg/dL');")
    con.execute("INSERT INTO person_tbl VALUES ('p1'), ('p2');")
    con.execute("INSERT INTO death_tbl VALUES ('p1', 'heart failure');")
    return con


def test_single_nested_same_row_becomes_a_struct(compiler: SQLCompiler, connection) -> None:
    """A nested derivation reading the parent's own row compiles to an inline struct.

    Shape 1: MeasurementObservation.value_quantity -> Quantity, both from `meas`.
    """
    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "MeasurementObservation": ClassDerivation(
                name="MeasurementObservation",
                populated_from="meas",
                slot_derivations={
                    "id": SlotDerivation(name="id", populated_from="meas_id"),
                    "value_quantity": SlotDerivation(
                        name="value_quantity",
                        class_derivations=[_quantity_derivation("Quantity", "meas", "meas_value", "meas_unit")],
                    ),
                },
            ),
        },
    )
    connection.execute(compiler.compile(spec).serialization)
    rows = connection.execute(
        "SELECT id, value_quantity.value, value_quantity.unit FROM MeasurementObservation ORDER BY id;"
    ).fetchall()
    assert rows == [("m1", 1.5, "mg/dL"), ("m2", 2.5, "mg/dL")]


def test_two_level_nesting_across_a_join(compiler: SQLCompiler, connection) -> None:
    """Nesting recurses: an Assay struct carries Quantity structs of its own.

    Shape 2: MeasurementObservation.associated_assay -> Assay (joined from `assay_tbl`),
    whose limits of detection are themselves Quantity.
    """
    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "MeasurementObservation": ClassDerivation(
                name="MeasurementObservation",
                populated_from="meas",
                joins={"assay_tbl": {"alias": "assay_tbl", "join_on": "assay_id"}},
                slot_derivations={
                    "id": SlotDerivation(name="id", populated_from="meas_id"),
                    "associated_assay": SlotDerivation(
                        name="associated_assay",
                        class_derivations=[
                            ClassDerivation(
                                name="Assay",
                                populated_from="assay_tbl",
                                slot_derivations={
                                    "id": SlotDerivation(name="id", populated_from="assay_id"),
                                    "name": SlotDerivation(name="name", populated_from="assay_name"),
                                    "lower_limit_of_detection": SlotDerivation(
                                        name="lower_limit_of_detection",
                                        class_derivations=[
                                            _quantity_derivation("Quantity", "assay_tbl", "lower_value", "lower_unit")
                                        ],
                                    ),
                                    "upper_limit_of_detection": SlotDerivation(
                                        name="upper_limit_of_detection",
                                        class_derivations=[
                                            _quantity_derivation("Quantity", "assay_tbl", "upper_value", "upper_unit")
                                        ],
                                    ),
                                },
                            )
                        ],
                    ),
                },
            ),
        },
    )
    connection.execute(compiler.compile(spec).serialization)
    rows = connection.execute(
        "SELECT id, associated_assay.name, "
        "associated_assay.lower_limit_of_detection.value, "
        "associated_assay.upper_limit_of_detection.unit "
        "FROM MeasurementObservation ORDER BY id;"
    ).fetchall()
    assert rows == [
        ("m1", "glucose panel", 0.5, "mg/dL"),
        ("m2", "glucose panel", 0.5, "mg/dL"),
    ]


def test_multivalued_nested_becomes_a_list_of_structs(compiler: SQLCompiler, connection) -> None:
    """A multivalued nested derivation across a join compiles to a list of structs.

    Shape 3: MeasurementObservationSet.observations -> [MeasurementObservation], joined
    from `meas`, each carrying a nested Quantity of its own.
    """
    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "MeasurementObservationSet": ClassDerivation(
                name="MeasurementObservationSet",
                populated_from="obs_set",
                joins={"meas": {"alias": "meas", "join_on": "set_id"}},
                slot_derivations={
                    "id": SlotDerivation(name="id", populated_from="set_id"),
                    "observations": SlotDerivation(
                        name="observations",
                        class_derivations=[
                            ClassDerivation(
                                name="MeasurementObservation",
                                populated_from="meas",
                                slot_derivations={
                                    "id": SlotDerivation(name="id", populated_from="meas_id"),
                                    "value_quantity": SlotDerivation(
                                        name="value_quantity",
                                        class_derivations=[
                                            _quantity_derivation("Quantity", "meas", "meas_value", "meas_unit")
                                        ],
                                    ),
                                },
                            )
                        ],
                    ),
                },
            ),
        },
    )
    connection.execute(compiler.compile(spec).serialization)
    rows = connection.execute("SELECT id, observations FROM MeasurementObservationSet WHERE id = 's1';").fetchall()
    assert rows == [
        (
            "s1",
            [
                {"id": "m1", "value_quantity": {"value": 1.5, "unit": "mg/dL"}, "associated_assay": None},
                {"id": "m2", "value_quantity": {"value": 2.5, "unit": "mg/dL"}, "associated_assay": None},
            ],
        )
    ]


def test_multivalued_nested_is_empty_when_the_join_misses(compiler: SQLCompiler, connection) -> None:
    """A parent with no matching child rows gets an empty list, not a hollow struct.

    Shape 4: Person.cause_of_death is emitted for living participants too.  Matching the
    Python backend, a join miss yields [] rather than NULL or a struct of nulls (#217).
    """
    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "Person": ClassDerivation(
                name="Person",
                populated_from="person_tbl",
                joins={
                    "death_tbl": {
                        "alias": "death_tbl",
                        "source_key": "person_id",
                        "lookup_key": "d_person_id",
                    }
                },
                slot_derivations={
                    "id": SlotDerivation(name="id", populated_from="person_id"),
                    "cause_of_death": SlotDerivation(
                        name="cause_of_death",
                        class_derivations=[
                            ClassDerivation(
                                name="CauseOfDeath",
                                populated_from="death_tbl",
                                slot_derivations={
                                    "cause": SlotDerivation(name="cause", populated_from="cause"),
                                },
                            )
                        ],
                    ),
                },
            ),
        },
    )
    connection.execute(compiler.compile(spec).serialization)
    rows = connection.execute("SELECT id, cause_of_death FROM Person ORDER BY id;").fetchall()
    assert rows == [
        ("p1", [{"cause": "heart failure"}]),
        ("p2", []),
    ]


def test_map_database_writes_nested_structs_to_the_target(
    source_schemaview: SchemaView, target_schemaview: SchemaView, connection
) -> None:
    """End-to-end: DuckDBTransformer.map_database lands nested structs in the target table.

    Previously the compiled INSERTs ran against the source connection, so the target held
    nothing but its DDL, and the two connections opened on ':memory:' were separate databases.
    """
    from linkml_map.transformer.duckdb_transformer import DuckDBTransformer

    tr = DuckDBTransformer()
    tr.source_schemaview = source_schemaview
    tr.target_schemaview = target_schemaview
    tr.specification = TransformationSpecification(
        id="test",
        class_derivations={
            "MeasurementObservation": ClassDerivation(
                name="MeasurementObservation",
                populated_from="meas",
                slot_derivations={
                    "id": SlotDerivation(name="id", populated_from="meas_id"),
                    "value_quantity": SlotDerivation(
                        name="value_quantity",
                        class_derivations=[_quantity_derivation("Quantity", "meas", "meas_value", "meas_unit")],
                    ),
                },
            ),
        },
    )
    result = tr.map_database(connection)
    rows = result.execute("SELECT id, value_quantity.value FROM MeasurementObservation ORDER BY id;").fetchall()
    assert rows == [("m1", 1.5), ("m2", 2.5)]


def test_map_database_rejects_a_separate_target_database(
    source_schemaview: SchemaView, target_schemaview: SchemaView
) -> None:
    """Writing to a database other than the source is refused rather than silently empty."""
    from linkml_map.transformer.duckdb_transformer import DuckDBTransformer

    tr = DuckDBTransformer()
    tr.source_schemaview = source_schemaview
    tr.target_schemaview = target_schemaview
    tr.specification = TransformationSpecification(id="test", class_derivations={})
    with pytest.raises(NotImplementedError, match="separate from the source"):
        tr.map_database("source.db", "target.db")


def test_inlined_class_range_becomes_a_struct_column(compiler: SQLCompiler, target_schemaview: SchemaView) -> None:
    """DDL for an inlined class-ranged slot is a STRUCT of that class's columns, not TEXT."""
    slot = target_schemaview.induced_slot("value_quantity", "MeasurementObservation")
    assert compiler.sql_type(slot, target_schemaview) == 'STRUCT("value" REAL, "unit" TEXT)'


def test_multivalued_inlined_class_range_becomes_a_struct_list(
    compiler: SQLCompiler, target_schemaview: SchemaView
) -> None:
    """A multivalued inlined class-ranged slot becomes STRUCT(...)[]."""
    slot = target_schemaview.induced_slot("cause_of_death", "Person")
    assert compiler.sql_type(slot, target_schemaview) == 'STRUCT("cause" TEXT)[]'


def test_noninlined_class_range_uses_the_identifier_type(compiler: SQLCompiler) -> None:
    """A non-inlined class-ranged slot is a reference, typed as its target's identifier.

    Previously this branch emitted JSON while the *inlined* branch emitted TEXT — the
    inverse of what each slot actually holds.
    """
    schema = TARGET_SCHEMA.replace(
        """      value_quantity:
        range: Quantity
        inlined: true""",
        """      value_quantity:
        range: Assay""",
    )
    sv = SchemaView(schema)
    slot = sv.induced_slot("value_quantity", "MeasurementObservation")
    assert compiler.sql_type(slot, sv) == "TEXT"


def test_recursive_range_degrades_to_json(compiler: SQLCompiler) -> None:
    """A class whose inlined range reaches itself cannot be an infinitely deep STRUCT."""
    schema = """
id: https://example.org/rec
name: rec
prefixes:
  linkml: https://w3id.org/linkml/
default_range: string
imports:
  - linkml:types
classes:
  Node:
    attributes:
      label:
      child:
        range: Node
        inlined: true
"""
    sv = SchemaView(schema)
    slot = sv.induced_slot("child", "Node")
    assert compiler.sql_type(slot, sv) == 'STRUCT("label" TEXT, "child" JSON)'


def test_cross_table_nesting_without_a_join_is_an_error(compiler: SQLCompiler) -> None:
    """A nested derivation from another table with no join spec must fail loudly.

    The previous fallback emitted `<slot> AS <slot>`, referencing a source column that does
    not exist — a binder error at execution, or silently wrong data if the name collides.
    """
    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "MeasurementObservation": ClassDerivation(
                name="MeasurementObservation",
                populated_from="meas",
                slot_derivations={
                    "associated_assay": SlotDerivation(
                        name="associated_assay",
                        class_derivations=[
                            ClassDerivation(name="Assay", populated_from="assay_tbl"),
                        ],
                    ),
                },
            ),
        },
    )
    with pytest.raises(ValueError, match="no join is declared"):
        compiler.compile(spec)


def test_nesting_without_a_target_schema_is_an_error(source_schemaview: SchemaView) -> None:
    """Nested derivations need the target schema to resolve cardinality, so say so."""
    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "MeasurementObservation": ClassDerivation(
                name="MeasurementObservation",
                populated_from="meas",
                slot_derivations={
                    "value_quantity": SlotDerivation(
                        name="value_quantity",
                        class_derivations=[_quantity_derivation("Quantity", "meas", "meas_value", "meas_unit")],
                    ),
                },
            ),
        },
    )
    with pytest.raises(ValueError, match="requires a target schema"):
        SQLCompiler(source_schemaview=source_schemaview).compile(spec)


def test_multiple_nested_derivations_on_a_single_valued_slot_is_an_error(compiler: SQLCompiler) -> None:
    """Two nested derivations cannot collapse into one single-valued slot."""
    spec = TransformationSpecification(
        id="test",
        class_derivations={
            "MeasurementObservation": ClassDerivation(
                name="MeasurementObservation",
                populated_from="meas",
                slot_derivations={
                    "value_quantity": SlotDerivation(
                        name="value_quantity",
                        class_derivations=[
                            _quantity_derivation("Quantity", "meas", "meas_value", "meas_unit"),
                            _quantity_derivation("Quantity", "meas", "meas_value", "meas_unit"),
                        ],
                    ),
                },
            ),
        },
    )
    with pytest.raises(ValueError, match="single-valued"):
        compiler.compile(spec)
