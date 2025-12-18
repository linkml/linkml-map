"""Tests for the DataLoader class."""

import json
from pathlib import Path

import pytest
import yaml

from linkml_map.loaders import DataLoader, FileFormat, load_data_file


@pytest.fixture
def sample_tsv_file(tmp_path: Path) -> Path:
    """Create a sample TSV file."""
    tsv_path = tmp_path / "Person.tsv"
    content = "id\tname\tage\nP:001\tAlice\t30\nP:002\tBob\t25\n"
    tsv_path.write_text(content)
    return tsv_path


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Create a sample CSV file."""
    csv_path = tmp_path / "Person.csv"
    content = "id,name,age\nP:003,Charlie,35\nP:004,Diana,28\n"
    csv_path.write_text(content)
    return csv_path


@pytest.fixture
def sample_yaml_file(tmp_path: Path) -> Path:
    """Create a sample YAML file."""
    yaml_path = tmp_path / "Person.yaml"
    data = {"id": "P:005", "name": "Eve", "age": 22}
    yaml_path.write_text(yaml.dump(data))
    return yaml_path


@pytest.fixture
def sample_json_file(tmp_path: Path) -> Path:
    """Create a sample JSON file."""
    json_path = tmp_path / "Person.json"
    data = {"id": "P:006", "name": "Frank", "age": 40}
    json_path.write_text(json.dumps(data))
    return json_path


@pytest.fixture
def sample_data_dir(tmp_path: Path) -> Path:
    """Create a directory with multiple data files."""
    # TSV file
    tsv_path = tmp_path / "Person.tsv"
    tsv_path.write_text("id\tname\tage\nP:001\tAlice\t30\nP:002\tBob\t25\n")

    # Different entity type
    org_path = tmp_path / "Organization.csv"
    org_path.write_text("id,name,founded\nO:001,Acme Inc,1999\n")

    return tmp_path


class TestFileFormat:
    """Tests for FileFormat enum."""

    def test_from_extension_tsv(self) -> None:
        assert FileFormat.from_extension("file.tsv") == FileFormat.TSV

    def test_from_extension_csv(self) -> None:
        assert FileFormat.from_extension("file.csv") == FileFormat.CSV

    def test_from_extension_yaml(self) -> None:
        assert FileFormat.from_extension("file.yaml") == FileFormat.YAML
        assert FileFormat.from_extension("file.yml") == FileFormat.YAML

    def test_from_extension_json(self) -> None:
        assert FileFormat.from_extension("file.json") == FileFormat.JSON

    def test_from_extension_unsupported(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file extension"):
            FileFormat.from_extension("file.xml")


class TestDataLoaderSingleFile:
    """Tests for DataLoader in single-file mode."""

    def test_load_tsv_file(self, sample_tsv_file: Path) -> None:
        loader = DataLoader(sample_tsv_file)
        rows = list(loader)
        assert len(rows) == 2
        assert rows[0]["id"] == "P:001"
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == 30  # Should be parsed as int
        assert rows[1]["id"] == "P:002"
        assert rows[1]["name"] == "Bob"

    def test_load_csv_file(self, sample_csv_file: Path) -> None:
        loader = DataLoader(sample_csv_file)
        rows = list(loader)
        assert len(rows) == 2
        assert rows[0]["id"] == "P:003"
        assert rows[0]["name"] == "Charlie"

    def test_load_yaml_file(self, sample_yaml_file: Path) -> None:
        loader = DataLoader(sample_yaml_file)
        rows = list(loader)
        assert len(rows) == 1
        assert rows[0]["id"] == "P:005"
        assert rows[0]["name"] == "Eve"

    def test_load_json_file(self, sample_json_file: Path) -> None:
        loader = DataLoader(sample_json_file)
        rows = list(loader)
        assert len(rows) == 1
        assert rows[0]["id"] == "P:006"
        assert rows[0]["name"] == "Frank"

    def test_single_file_cannot_use_identifier(self, sample_tsv_file: Path) -> None:
        loader = DataLoader(sample_tsv_file)
        with pytest.raises(ValueError, match="Cannot use identifier-based access"):
            _ = loader["Person"]

    def test_is_single_file_property(self, sample_tsv_file: Path) -> None:
        loader = DataLoader(sample_tsv_file)
        assert loader.is_single_file is True

    def test_nonexistent_path_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError, match="Path not found"):
            DataLoader("/nonexistent/path/to/file.tsv")


class TestDataLoaderDirectory:
    """Tests for DataLoader in directory mode."""

    def test_load_by_identifier(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        rows = list(loader["Person"])
        assert len(rows) == 2
        assert rows[0]["id"] == "P:001"

    def test_load_different_identifiers(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        person_rows = list(loader["Person"])
        org_rows = list(loader["Organization"])
        assert len(person_rows) == 2
        assert len(org_rows) == 1
        assert org_rows[0]["name"] == "Acme Inc"

    def test_identifier_not_found(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        with pytest.raises(FileNotFoundError, match="No data file found"):
            _ = list(loader["NonExistent"])

    def test_contains(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        assert "Person" in loader
        assert "Organization" in loader
        assert "NonExistent" not in loader

    def test_get_available_identifiers(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        identifiers = loader.get_available_identifiers()
        assert "Organization" in identifiers
        assert "Person" in identifiers

    def test_load_all(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        all_data = loader.load_all()
        assert "Person" in all_data
        assert "Organization" in all_data
        assert len(all_data["Person"]) == 2
        assert len(all_data["Organization"]) == 1

    def test_directory_cannot_iterate_directly(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        with pytest.raises(ValueError, match="Cannot iterate directly"):
            _ = list(loader)

    def test_is_single_file_property_directory(self, sample_data_dir: Path) -> None:
        loader = DataLoader(sample_data_dir)
        assert loader.is_single_file is False


class TestIterSources:
    """Tests for the unified iter_sources method."""

    def test_single_file_iter_sources(self, sample_tsv_file: Path) -> None:
        """Single file should yield one source with filename stem as identifier."""
        loader = DataLoader(sample_tsv_file)
        sources = list(loader.iter_sources())

        assert len(sources) == 1
        identifier, rows = sources[0]
        assert identifier == "Person"  # From Person.tsv
        rows_list = list(rows)
        assert len(rows_list) == 2

    def test_directory_iter_sources(self, sample_data_dir: Path) -> None:
        """Directory should yield multiple sources, one per file."""
        loader = DataLoader(sample_data_dir)
        sources = dict(loader.iter_sources())

        assert "Person" in sources
        assert "Organization" in sources
        person_rows = list(sources["Person"])
        assert len(person_rows) == 2

    def test_iter_sources_unifies_single_and_directory(
        self, sample_tsv_file: Path, sample_data_dir: Path
    ) -> None:
        """Both modes should work identically through iter_sources."""
        # Single file
        single_loader = DataLoader(sample_tsv_file)
        single_sources = list(single_loader.iter_sources())

        # Directory (which contains Person.tsv among others)
        dir_loader = DataLoader(sample_data_dir)
        dir_sources = dict(dir_loader.iter_sources())

        # Both should have Person data accessible the same way
        single_id, single_rows = single_sources[0]
        assert single_id == "Person"

        dir_person_rows = list(dir_sources["Person"])
        single_person_rows = list(single_rows)

        # Same number of rows
        assert len(single_person_rows) == len(dir_person_rows)

    def test_single_file_in_cluttered_directory(self, tmp_path: Path) -> None:
        """Single file mode should only process the specified file, ignoring siblings."""
        # Create a directory with mixed files
        data_file = tmp_path / "people.tsv"
        data_file.write_text("id\tname\nP:001\tAlice\n")
        (tmp_path / "README.md").write_text("# Documentation")
        (tmp_path / "schema.yaml").write_text("id: test-schema")
        (tmp_path / "config.json").write_text('{"key": "value"}')

        # Point to specific file - should only process that file
        loader = DataLoader(data_file)
        sources = list(loader.iter_sources())

        assert len(sources) == 1
        identifier, rows = sources[0]
        assert identifier == "people"
        assert len(list(rows)) == 1


class TestDataLoaderFormatPriority:
    """Tests for file format priority in directory mode."""

    def test_tsv_takes_priority(self, tmp_path: Path) -> None:
        """TSV should be preferred over CSV when both exist."""
        # Create both TSV and CSV for same identifier
        tsv_path = tmp_path / "Person.tsv"
        csv_path = tmp_path / "Person.csv"
        tsv_path.write_text("id\tname\nP:TSV\tFrom TSV\n")
        csv_path.write_text("id,name\nP:CSV,From CSV\n")

        loader = DataLoader(tmp_path)
        rows = list(loader["Person"])
        assert len(rows) == 1
        assert rows[0]["id"] == "P:TSV"  # TSV takes priority

    def test_explicit_format_preference(self, tmp_path: Path) -> None:
        """Explicit default_format should override priority."""
        tsv_path = tmp_path / "Person.tsv"
        csv_path = tmp_path / "Person.csv"
        tsv_path.write_text("id\tname\nP:TSV\tFrom TSV\n")
        csv_path.write_text("id,name\nP:CSV,From CSV\n")

        loader = DataLoader(tmp_path, default_format=FileFormat.CSV)
        rows = list(loader["Person"])
        assert len(rows) == 1
        assert rows[0]["id"] == "P:CSV"  # CSV due to explicit preference


class TestLoadDataFile:
    """Tests for the load_data_file convenience function."""

    def test_load_tsv(self, sample_tsv_file: Path) -> None:
        rows = list(load_data_file(sample_tsv_file))
        assert len(rows) == 2

    def test_load_with_explicit_format(self, sample_tsv_file: Path) -> None:
        rows = list(load_data_file(sample_tsv_file, file_format=FileFormat.TSV))
        assert len(rows) == 2


class TestDataLoaderSkipEmptyRows:
    """Tests for skip_empty_rows behavior."""

    def test_skip_empty_rows_true(self, tmp_path: Path) -> None:
        tsv_path = tmp_path / "test.tsv"
        tsv_path.write_text("id\tname\nP:001\tAlice\n\nP:002\tBob\n")
        loader = DataLoader(tsv_path, skip_empty_rows=True)
        rows = list(loader)
        assert len(rows) == 2

    def test_skip_empty_rows_false(self, tmp_path: Path) -> None:
        # Note: Python's csv.DictReader skips empty lines regardless of skip_empty_rows setting
        # So we test that rows with empty values are handled correctly
        tsv_path = tmp_path / "test.tsv"
        tsv_path.write_text("id\tname\nP:001\tAlice\nP:002\t\n")  # P:002 has empty name
        loader = DataLoader(tsv_path, skip_empty_rows=False)
        rows = list(loader)
        assert len(rows) == 2
        assert rows[1]["id"] == "P:002"
        # Empty string values are not included in the dict by linkml's loader
        assert "name" not in rows[1] or rows[1].get("name") == ""
