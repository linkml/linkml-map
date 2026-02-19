"""Integration tests for CLI with tabular (TSV/CSV) input."""

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from linkml_map.cli.cli import main

# Test data directory
TABULAR_TEST_DIR = Path(__file__).parent.parent / "input" / "examples" / "tabular"
TABULAR_DATA_DIR = TABULAR_TEST_DIR / "data"
TABULAR_SOURCE_SCHEMA = TABULAR_TEST_DIR / "source" / "person_flat.yaml"
TABULAR_TRANSFORM = TABULAR_TEST_DIR / "transform" / "person_to_agent.transform.yaml"


@pytest.fixture
def runner() -> CliRunner:
    """Command line interface test runner."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def sample_tsv_data(tmp_path: Path) -> Path:
    """Create sample TSV data file."""
    tsv_path = tmp_path / "Person.tsv"
    content = "id\tname\tprimary_email\tage_in_years\tgender\n"
    content += "P:001\tAlice\talice@example.com\t30\tcisgender woman\n"
    content += "P:002\tBob\tbob@example.com\t25\tcisgender man\n"
    tsv_path.write_text(content)
    return tsv_path


@pytest.fixture
def sample_csv_data(tmp_path: Path) -> Path:
    """Create sample CSV data file."""
    csv_path = tmp_path / "Person.csv"
    content = "id,name,primary_email,age_in_years,gender\n"
    content += "P:003,Charlie,charlie@example.com,35,cisgender man\n"
    csv_path.write_text(content)
    return csv_path


@pytest.fixture
def sample_schema(tmp_path: Path) -> Path:
    """Create sample schema file."""
    schema_path = tmp_path / "schema.yaml"
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
                    "primary_email": {},
                    "age_in_years": {"range": "integer"},
                    "gender": {},
                }
            }
        },
    }
    schema_path.write_text(yaml.dump(schema))
    return schema_path


@pytest.fixture
def sample_transform(tmp_path: Path) -> Path:
    """Create sample transformation spec."""
    transform_path = tmp_path / "transform.yaml"
    transform = {
        "id": "test-transform",
        "class_derivations": {
            "Agent": {
                "populated_from": "Person",
                "slot_derivations": {
                    "id": {},
                    "label": {"populated_from": "name"},
                    "email": {"populated_from": "primary_email"},
                    "age": {"expr": "str({age_in_years}) + ' years'"},
                },
            }
        },
    }
    transform_path.write_text(yaml.dump(transform))
    return transform_path


class TestMapDataTsv:
    """Tests for map-data command with TSV input."""

    def test_tsv_input_yaml_output(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
    ) -> None:
        """Test TSV input with default YAML output."""
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0
        # Output should contain transformed data
        assert "label: Alice" in result.stdout
        assert "label: Bob" in result.stdout

    def test_tsv_input_jsonl_output(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
    ) -> None:
        """Test TSV input with JSONL output."""
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-f",
                "jsonl",
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0
        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) == 2  # Two rows in TSV
        # Each line should be valid JSON
        for line in lines:
            obj = json.loads(line)
            assert "id" in obj
            assert "label" in obj

    def test_tsv_input_tsv_output(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
    ) -> None:
        """Test TSV input with TSV output."""
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-f",
                "tsv",
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3  # Header + 2 data rows
        # Check header
        assert "id" in lines[0]
        assert "label" in lines[0]
        # Check tab separation
        assert "\t" in lines[0]


class TestMapDataCsv:
    """Tests for map-data command with CSV input."""

    def test_csv_input_json_output(
        self,
        runner: CliRunner,
        sample_csv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
    ) -> None:
        """Test CSV input with JSON output."""
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-f",
                "json",
                str(sample_csv_data),
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["label"] == "Charlie"

    def test_csv_input_csv_output(
        self,
        runner: CliRunner,
        sample_csv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
    ) -> None:
        """Test CSV input with CSV output."""
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-f",
                "csv",
                str(sample_csv_data),
            ],
        )
        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data row
        # Check comma separation
        assert "," in lines[0]


class TestMapDataDirectory:
    """Tests for map-data command with directory input."""

    def test_directory_input(
        self,
        runner: CliRunner,
        sample_schema: Path,
        sample_transform: Path,
        tmp_path: Path,
    ) -> None:
        """Test directory input with multiple files."""
        # Create data directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create Person.tsv
        person_tsv = data_dir / "Person.tsv"
        person_tsv.write_text("id\tname\tprimary_email\tage_in_years\tgender\n")
        person_tsv.write_text(person_tsv.read_text() + "P:001\tAlice\talice@example.com\t30\tcisgender woman\n")

        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "-f",
                "jsonl",
                str(data_dir),
            ],
        )
        assert result.exit_code == 0
        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) >= 1


class TestMapDataOutputFile:
    """Tests for map-data command with output file."""

    def test_output_to_file(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
        tmp_path: Path,
    ) -> None:
        """Test writing output to a file."""
        output_file = tmp_path / "output.jsonl"
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-o",
                str(output_file),
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        # Should have JSONL content (inferred from .jsonl extension)
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 2

    def test_output_format_inferred_from_extension(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
        tmp_path: Path,
    ) -> None:
        """Test that output format is inferred from file extension."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-o",
                str(output_file),
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0
        content = output_file.read_text()
        # Should be valid JSON array
        data = json.loads(content)
        assert len(data) == 2


class TestMapDataAdditionalOutput:
    """Tests for -O / --additional-output flag."""

    def test_additional_output_tsv_and_json(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
        tmp_path: Path,
    ) -> None:
        """Test writing primary JSONL to file plus additional TSV and JSON outputs."""
        primary = tmp_path / "primary.jsonl"
        extra_tsv = tmp_path / "extra.tsv"
        extra_json = tmp_path / "extra.json"
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-o",
                str(primary),
                "-O",
                str(extra_tsv),
                "-O",
                str(extra_json),
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0, result.stderr

        # Primary JSONL
        jsonl_lines = [l for l in primary.read_text().strip().split("\n") if l]
        assert len(jsonl_lines) == 2
        for line in jsonl_lines:
            obj = json.loads(line)
            assert "id" in obj

        # Additional TSV
        tsv_lines = extra_tsv.read_text().strip().split("\n")
        assert len(tsv_lines) == 3  # header + 2 rows
        assert "\t" in tsv_lines[0]

        # Additional JSON
        json_data = json.loads(extra_json.read_text())
        assert len(json_data) == 2

    def test_additional_output_format_inferred(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
        tmp_path: Path,
    ) -> None:
        """Test that format is correctly inferred from extension for -O."""
        extra_jsonl = tmp_path / "out.jsonl"
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-f",
                "yaml",
                "-O",
                str(extra_jsonl),
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0, result.stderr

        # stdout should have YAML
        assert "label:" in result.stdout

        # Additional JSONL file
        jsonl_lines = [l for l in extra_jsonl.read_text().strip().split("\n") if l]
        assert len(jsonl_lines) == 2
        for line in jsonl_lines:
            json.loads(line)  # should not raise

    def test_additional_output_stdout_primary(
        self,
        runner: CliRunner,
        sample_tsv_data: Path,
        sample_schema: Path,
        sample_transform: Path,
        tmp_path: Path,
    ) -> None:
        """Test -O with primary output going to stdout (no -o)."""
        extra_json = tmp_path / "extra.json"
        result = runner.invoke(
            main,
            [
                "map-data",
                "-T",
                str(sample_transform),
                "-s",
                str(sample_schema),
                "--source-type",
                "Person",
                "-f",
                "jsonl",
                "-O",
                str(extra_json),
                str(sample_tsv_data),
            ],
        )
        assert result.exit_code == 0, result.stderr

        # stdout should have JSONL
        stdout_lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(stdout_lines) == 2

        # Additional JSON file
        json_data = json.loads(extra_json.read_text())
        assert len(json_data) == 2


class TestMapDataWithExistingTestData:
    """Tests using the existing test fixtures."""

    def test_with_tabular_test_fixtures(self, runner: CliRunner) -> None:
        """Test with the tabular test fixtures in the repo."""
        if not TABULAR_TEST_DIR.exists():
            pytest.skip("Tabular test fixtures not found")

        tsv_file = TABULAR_DATA_DIR / "Person.tsv"
        if not tsv_file.exists():
            pytest.skip("Person.tsv not found")

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
                "jsonl",
                str(tsv_file),
            ],
        )
        assert result.exit_code == 0
        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) >= 1
        # Verify content
        first = json.loads(lines[0])
        assert "id" in first
        assert "label" in first
