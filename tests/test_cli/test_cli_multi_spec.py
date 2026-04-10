"""Integration tests for multi-spec loading, --entity filter, and --emit-spec."""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from linkml_map.cli.cli import main

TABULAR_TEST_DIR = Path(__file__).parent.parent / "input" / "examples" / "tabular"
TABULAR_SOURCE_SCHEMA = TABULAR_TEST_DIR / "source" / "person_flat.yaml"
TABULAR_TRANSFORM = TABULAR_TEST_DIR / "transform" / "person_to_agent.transform.yaml"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture
def sample_tsv(tmp_path: Path) -> Path:
    tsv = tmp_path / "Person.tsv"
    tsv.write_text(
        "id\tname\tprimary_email\tage_in_years\tgender\n"
        "P:001\tAlice\talice@example.com\t30\tcisgender woman\n"
        "P:002\tBob\tbob@example.com\t25\tcisgender man\n"
    )
    return tsv


@pytest.fixture
def simple_schema(tmp_path: Path) -> Path:
    schema = {
        "id": "https://example.org/test",
        "name": "test",
        "prefixes": {"linkml": "https://w3id.org/linkml/"},
        "imports": ["linkml:types"],
        "default_range": "string",
        "classes": {
            "Person": {
                "attributes": {
                    "id": {"identifier": True},
                    "name": {},
                },
            },
            "Org": {
                "attributes": {
                    "id": {"identifier": True},
                    "title": {},
                },
            },
        },
    }
    p = tmp_path / "schema.yaml"
    p.write_text(yaml.dump(schema))
    return p


@pytest.fixture
def split_specs(tmp_path: Path) -> Path:
    """Create split spec files: one for Person, one for Org."""
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    (spec_dir / "person.yaml").write_text(
        yaml.dump(
            {
                "class_derivations": {
                    "Person": {
                        "populated_from": "Person",
                        "slot_derivations": {
                            "id": {},
                            "name": {},
                        },
                    }
                }
            }
        )
    )
    (spec_dir / "org.yaml").write_text(
        yaml.dump(
            {
                "class_derivations": {
                    "Org": {
                        "populated_from": "Org",
                        "slot_derivations": {
                            "id": {},
                            "title": {},
                        },
                    }
                }
            }
        )
    )
    return spec_dir


# --- Multi-T tests ---


def test_multi_t_single_file(runner: CliRunner, sample_tsv: Path) -> None:
    """Single -T still works."""
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(TABULAR_TRANSFORM),
            "-s",
            str(TABULAR_SOURCE_SCHEMA),
            "--source-type",
            "Person",
            "-f",
            "yaml",
            str(sample_tsv),
        ],
    )
    assert result.exit_code == 0, result.stderr


def test_multi_t_directory(
    runner: CliRunner,
    split_specs: Path,
    simple_schema: Path,
    tmp_path: Path,
) -> None:
    """Passing a directory as -T loads and merges all specs."""
    tsv = tmp_path / "Person.tsv"
    tsv.write_text("id\tname\nP:001\tAlice\n")
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(split_specs),
            "-s",
            str(simple_schema),
            "--source-type",
            "Person",
            "-f",
            "yaml",
            str(tsv),
        ],
    )
    assert result.exit_code == 0, result.stderr


def test_multi_t_multiple_files(
    runner: CliRunner,
    split_specs: Path,
    simple_schema: Path,
    tmp_path: Path,
) -> None:
    """Multiple -T flags merge specs."""
    tsv = tmp_path / "Person.tsv"
    tsv.write_text("id\tname\nP:001\tAlice\n")
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(split_specs / "person.yaml"),
            "-T",
            str(split_specs / "org.yaml"),
            "-s",
            str(simple_schema),
            "--source-type",
            "Person",
            "-f",
            "yaml",
            str(tsv),
        ],
    )
    assert result.exit_code == 0, result.stderr


# --- --entity tests ---


def test_entity_filter_streaming(
    runner: CliRunner,
    split_specs: Path,
    simple_schema: Path,
    tmp_path: Path,
) -> None:
    """--entity filters to only the specified class_derivation."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "Person.tsv").write_text("id\tname\nP:001\tAlice\n")
    (data_dir / "Org.tsv").write_text("id\ttitle\nO:001\tAcme\n")
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(split_specs),
            "-s",
            str(simple_schema),
            "--entity",
            "Person",
            "-f",
            "jsonl",
            str(data_dir),
        ],
    )
    assert result.exit_code == 0, result.stderr
    lines = [line for line in result.output.strip().split("\n") if line]
    assert len(lines) == 1
    import json

    obj = json.loads(lines[0])
    assert obj["name"] == "Alice"


def test_entity_filter_excludes_other(
    runner: CliRunner,
    split_specs: Path,
    simple_schema: Path,
    tmp_path: Path,
) -> None:
    """--entity Org should not produce Person records."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "Person.tsv").write_text("id\tname\nP:001\tAlice\n")
    (data_dir / "Org.tsv").write_text("id\ttitle\nO:001\tAcme\n")
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(split_specs),
            "-s",
            str(simple_schema),
            "--entity",
            "Org",
            "-f",
            "jsonl",
            str(data_dir),
        ],
    )
    assert result.exit_code == 0, result.stderr
    lines = [line for line in result.output.strip().split("\n") if line]
    assert len(lines) == 1
    import json

    obj = json.loads(lines[0])
    assert obj["title"] == "Acme"


# --- --emit-spec tests ---


def test_emit_spec_on_map_data(
    runner: CliRunner,
    split_specs: Path,
    simple_schema: Path,
    tmp_path: Path,
) -> None:
    """--emit-spec writes the resolved spec to a file."""
    tsv = tmp_path / "Person.tsv"
    tsv.write_text("id\tname\nP:001\tAlice\n")
    emit_path = tmp_path / "resolved.yaml"
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(split_specs),
            "-s",
            str(simple_schema),
            "--source-type",
            "Person",
            "--emit-spec",
            str(emit_path),
            "-f",
            "yaml",
            str(tsv),
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert emit_path.exists()
    emitted = yaml.safe_load(emit_path.read_text())
    assert "class_derivations" in emitted


def test_emit_spec_with_entity_filter(
    runner: CliRunner,
    split_specs: Path,
    simple_schema: Path,
    tmp_path: Path,
) -> None:
    """--emit-spec + --entity only includes the filtered class."""
    tsv = tmp_path / "Person.tsv"
    tsv.write_text("id\tname\nP:001\tAlice\n")
    emit_path = tmp_path / "resolved.yaml"
    result = runner.invoke(
        main,
        [
            "map-data",
            "-T",
            str(split_specs),
            "-s",
            str(simple_schema),
            "--entity",
            "Person",
            "--emit-spec",
            str(emit_path),
            "-f",
            "yaml",
            str(tsv),
        ],
    )
    assert result.exit_code == 0, result.stderr
    emitted = yaml.safe_load(emit_path.read_text())
    cd_names = [cd["name"] for cd in emitted["class_derivations"]]
    assert cd_names == ["Person"]


# --- validate-spec tests ---


def test_validate_spec_merge(runner: CliRunner, split_specs: Path) -> None:
    """--merge validates all specs as a combined spec."""
    result = runner.invoke(
        main,
        ["validate-spec", "--merge", str(split_specs / "person.yaml"), str(split_specs / "org.yaml")],
    )
    assert result.exit_code == 0, result.stderr
    assert "ok" in result.output


def test_validate_spec_merge_emit_to_file(runner: CliRunner, split_specs: Path, tmp_path: Path) -> None:
    """--merge --emit-spec PATH writes the resolved spec to a file."""
    emit_path = tmp_path / "resolved.yaml"
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--merge",
            "--emit-spec",
            str(emit_path),
            str(split_specs / "person.yaml"),
            str(split_specs / "org.yaml"),
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert emit_path.exists()
    emitted = yaml.safe_load(emit_path.read_text())
    assert "class_derivations" in emitted


def test_validate_spec_merge_emit_stdout(runner: CliRunner, split_specs: Path) -> None:
    """--merge --emit-spec - writes the resolved spec to stdout."""
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--merge",
            "--emit-spec",
            "-",
            str(split_specs / "person.yaml"),
            str(split_specs / "org.yaml"),
        ],
    )
    assert result.exit_code == 0, result.stderr
    output_after_ok = result.output.split("Merged spec: ok\n", 1)[1]
    emitted = yaml.safe_load(output_after_ok)
    assert "class_derivations" in emitted


def test_validate_spec_merge_emit_entity(runner: CliRunner, split_specs: Path, tmp_path: Path) -> None:
    """--merge --emit-spec --entity filters the emitted spec."""
    emit_path = tmp_path / "resolved.yaml"
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--merge",
            "--emit-spec",
            str(emit_path),
            "--entity",
            "Person",
            str(split_specs / "person.yaml"),
            str(split_specs / "org.yaml"),
        ],
    )
    assert result.exit_code == 0, result.stderr
    emitted = yaml.safe_load(emit_path.read_text())
    cd_names = [cd["name"] for cd in emitted["class_derivations"]]
    assert cd_names == ["Person"]


def test_validate_spec_entity_without_merge_errors(runner: CliRunner, split_specs: Path) -> None:
    """--entity without --merge should error."""
    result = runner.invoke(
        main,
        ["validate-spec", "--entity", "Person", str(split_specs / "person.yaml")],
    )
    assert result.exit_code == 1
    assert "--merge" in result.stderr
