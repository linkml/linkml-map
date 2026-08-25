"""
Tests for Parquet and DuckDB output, which are built by DuckDB from staged JSON Lines.

The property that matters is that nesting survives as typed columns: a nested object
becomes a STRUCT and a list of them a STRUCT[], so a consumer reads a nested field with a
column access rather than a join.
"""

from pathlib import Path

import duckdb
import pytest

from linkml_map.writers.output_streams import (
    EXTENSION_FORMAT_MAP,
    MultiStreamWriter,
    OutputFormat,
    make_stream_writer,
)

NESTED_ROWS = [
    {
        "id": "m1",
        "observation_type": "OBA:VT0001253",
        "value_quantity": {"value_decimal": 155.448, "unit": "cm"},
    },
    {
        "id": "m2",
        "observation_type": "OBA:VT0001253",
        "value_quantity": {"value_decimal": 167.386, "unit": "cm"},
    },
]


def _write(rows: list[dict], target: Path, fmt: OutputFormat, **kwargs) -> None:
    """Stream *rows* to *target* in *fmt* through the normal writer path."""
    writer = make_stream_writer(fmt, **kwargs)
    MultiStreamWriter([(writer, target)]).write_all(iter([rows]))


@pytest.mark.parametrize(
    ("extension", "expected"),
    [(".parquet", OutputFormat.PARQUET), (".duckdb", OutputFormat.DUCKDB)],
)
def test_extension_maps_to_format(extension: str, expected: OutputFormat) -> None:
    """A .parquet/.duckdb output path selects the columnar writer without an explicit flag."""
    assert EXTENSION_FORMAT_MAP[extension] == expected


def test_parquet_preserves_nesting_as_a_struct_column(tmp_path: Path) -> None:
    """A nested object round-trips into Parquet as a STRUCT, readable by column access."""
    target = tmp_path / "obs.parquet"
    _write(NESTED_ROWS, target, OutputFormat.PARQUET)

    con = duckdb.connect()
    types = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{target}')").fetchall()}
    assert types["value_quantity"] == "STRUCT(value_decimal DOUBLE, unit VARCHAR)"
    rows = con.execute(
        f"SELECT id, value_quantity.unit, value_quantity.value_decimal FROM read_parquet('{target}') ORDER BY id"
    ).fetchall()
    assert rows == [("m1", "cm", 155.448), ("m2", "cm", 167.386)]


def test_parquet_target_holds_no_staging_file(tmp_path: Path) -> None:
    """The staging JSONL is removed, leaving only the artifact."""
    target = tmp_path / "obs.parquet"
    _write(NESTED_ROWS, target, OutputFormat.PARQUET)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["obs.parquet"]


def test_duckdb_writes_a_queryable_table(tmp_path: Path) -> None:
    """DuckDB output lands a table named for the file stem by default."""
    target = tmp_path / "phs000000.duckdb"
    _write(NESTED_ROWS, target, OutputFormat.DUCKDB)

    con = duckdb.connect(str(target))
    assert [r[0] for r in con.execute("SHOW TABLES").fetchall()] == ["phs000000"]
    rows = con.execute('SELECT id, value_quantity.unit FROM "phs000000" ORDER BY id').fetchall()
    assert rows == [("m1", "cm"), ("m2", "cm")]


def test_duckdb_table_name_override(tmp_path: Path) -> None:
    """--table-name controls the table, so several classes can share one database file."""
    target = tmp_path / "phs000000.duckdb"
    _write(NESTED_ROWS, target, OutputFormat.DUCKDB, table_name="measurement_observation")
    con = duckdb.connect(str(target))
    assert [r[0] for r in con.execute("SHOW TABLES").fetchall()] == ["measurement_observation"]


def test_duckdb_accumulates_tables_across_runs(tmp_path: Path) -> None:
    """Repeated runs against one file add tables rather than replacing the database.

    This is how a per-study database covering several target classes gets built.
    """
    target = tmp_path / "phs000000.duckdb"
    _write(NESTED_ROWS, target, OutputFormat.DUCKDB, table_name="measurement_observation")
    _write([{"id": "p1", "sex": "F"}], target, OutputFormat.DUCKDB, table_name="participant")

    con = duckdb.connect(str(target))
    tables = sorted(r[0] for r in con.execute("SHOW TABLES").fetchall())
    assert tables == ["measurement_observation", "participant"]
    assert con.execute('SELECT count(*) FROM "measurement_observation"').fetchone() == (2,)


def test_multivalued_nesting_becomes_a_struct_list(tmp_path: Path) -> None:
    """A list of nested objects becomes STRUCT[], not a normalized side table."""
    rows = [
        {
            "id": "s1",
            "observations": [
                {"id": "m1", "value": 1.5},
                {"id": "m2", "value": 2.5},
            ],
        }
    ]
    target = tmp_path / "sets.parquet"
    _write(rows, target, OutputFormat.PARQUET)

    con = duckdb.connect()
    types = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{target}')").fetchall()}
    assert types["observations"] == 'STRUCT(id VARCHAR, "value" DOUBLE)[]'
    assert con.execute(f"SELECT observations[1].id FROM read_parquet('{target}')").fetchone() == ("m1",)


def test_empty_stream_writes_an_empty_artifact(tmp_path: Path) -> None:
    """A transform yielding no rows still produces a readable file, not a crash."""
    target = tmp_path / "empty.parquet"
    _write([], target, OutputFormat.PARQUET)
    con = duckdb.connect()
    assert con.execute(f"SELECT count(*) FROM read_parquet('{target}')").fetchone() == (0,)


def test_columnar_output_alongside_other_formats(tmp_path: Path) -> None:
    """Parquet works as an additional -O target beside a text primary output."""
    jsonl_target = tmp_path / "obs.jsonl"
    parquet_target = tmp_path / "obs.parquet"
    outputs = [
        (make_stream_writer(OutputFormat.JSONL), jsonl_target),
        (make_stream_writer(OutputFormat.PARQUET), parquet_target),
    ]
    MultiStreamWriter(outputs).write_all(iter([NESTED_ROWS]))

    assert len(jsonl_target.read_text().strip().splitlines()) == 2
    con = duckdb.connect()
    assert con.execute(f"SELECT count(*) FROM read_parquet('{parquet_target}')").fetchone() == (2,)
