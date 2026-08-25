"""CLI tests for Parquet and DuckDB output across both input paths."""

from pathlib import Path

import duckdb
import pytest
from click.testing import CliRunner

from linkml_map.cli.cli import main

TABULAR_TEST_DIR = Path(__file__).parent.parent / "input" / "examples" / "tabular"
TABULAR_DATA = TABULAR_TEST_DIR / "data" / "Person.tsv"
TABULAR_SOURCE_SCHEMA = TABULAR_TEST_DIR / "source" / "person_flat.yaml"
TABULAR_TRANSFORM = TABULAR_TEST_DIR / "transform" / "person_to_agent.transform.yaml"


@pytest.fixture
def runner() -> CliRunner:
    """Command line interface test runner."""
    return CliRunner()


def _args(output: Path | None, *extra: str) -> list[str]:
    """Build a map-data invocation over the shared tabular fixture."""
    args = [
        "map-data",
        "-T",
        str(TABULAR_TRANSFORM),
        "-s",
        str(TABULAR_SOURCE_SCHEMA),
        "--source-type",
        "Person",
    ]
    if output is not None:
        args += ["-o", str(output)]
    return [*args, *extra, str(TABULAR_DATA)]


def test_table_name_applies_to_additional_duckdb_outputs(runner: CliRunner, tmp_path: Path) -> None:
    """--table-name reaches -O DuckDB writers, not just the primary output.

    Previously _build_additional_outputs built its writers without the table name, so an
    -O DuckDB file silently fell back to being named after the file stem.
    """
    primary = tmp_path / "primary.duckdb"
    extra = tmp_path / "extra.duckdb"
    result = runner.invoke(main, _args(primary, "--table-name", "agent", "-O", str(extra)))
    assert result.exit_code == 0, result.output

    for path in (primary, extra):
        con = duckdb.connect(str(path))
        assert [r[0] for r in con.execute("SHOW TABLES").fetchall()] == ["agent"]
        con.close()


def test_single_object_input_writes_parquet(runner: CliRunner, tmp_path: Path) -> None:
    """A single YAML input infers parquet from the extension and writes it.

    The non-streaming path used to reach dump_output, which raised NotImplementedError
    for formats it had no branch for.
    """
    source_data = tmp_path / "person.yaml"
    source_data.write_text(
        "id: P:001\nname: fred bloggs\nprimary_email: fred@example.com\nage_in_years: 33\ngender: nonbinary man\n"
    )
    target = tmp_path / "agent.parquet"
    result = runner.invoke(main, _args(target)[:-1] + [str(source_data)])
    assert result.exit_code == 0, result.output

    con = duckdb.connect()
    rows = con.execute(f"SELECT id, label FROM read_parquet('{target}')").fetchall()
    assert rows == [("P:001", "fred bloggs")]


def test_single_object_input_writes_duckdb_with_table_name(runner: CliRunner, tmp_path: Path) -> None:
    """--table-name is honored on the single-object path too."""
    source_data = tmp_path / "person.yaml"
    source_data.write_text(
        "id: P:002\nname: jane doe\nprimary_email: jane@example.com\nage_in_years: 28\ngender: cisgender woman\n"
    )
    target = tmp_path / "study.duckdb"
    result = runner.invoke(main, _args(target)[:-1] + ["--table-name", "agent", str(source_data)])
    assert result.exit_code == 0, result.output

    con = duckdb.connect(str(target))
    assert [r[0] for r in con.execute("SHOW TABLES").fetchall()] == ["agent"]
    assert con.execute("SELECT id FROM agent").fetchall() == [("P:002",)]


@pytest.mark.parametrize("fmt", ["parquet", "duckdb"])
def test_columnar_without_an_output_file_fails_cleanly(runner: CliRunner, fmt: str) -> None:
    """These artifacts are binary files DuckDB writes, so stdout is not an option.

    The failure must be a CLI error, not a traceback.
    """
    result = runner.invoke(main, _args(None, "--output-format", fmt))
    assert result.exit_code != 0
    assert "requires an output file" in result.output
    assert "Traceback" not in result.output
