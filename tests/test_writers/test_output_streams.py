"""Tests for output stream functions."""

import json

import pytest
import yaml

from linkml_map.writers import (
    OutputFormat,
    csv_stream,
    get_stream_writer,
    json_stream,
    jsonl_stream,
    tsv_stream,
    yaml_stream,
)
from linkml_map.writers.output_streams import TabularStreamWriter


@pytest.fixture
def sample_chunks():
    """Sample data chunks for testing."""
    return iter(
        [
            [
                {"id": "P:001", "name": "Alice", "age": 30},
                {"id": "P:002", "name": "Bob", "age": 25},
            ],
            [
                {"id": "P:003", "name": "Charlie", "age": 35},
            ],
        ]
    )


@pytest.fixture
def nested_chunks():
    """Sample data with nested objects."""
    return iter(
        [
            [
                {"id": "P:001", "name": "Alice", "address": {"street": "123 Main", "city": "Boston"}},
            ],
        ]
    )


class TestYamlStream:
    """Tests for yaml_stream function."""

    def test_basic_output(self, sample_chunks) -> None:
        result = "".join(yaml_stream(sample_chunks))
        # Should contain YAML document separators
        assert "---" in result
        assert "id:" in result or "id: P:001" in result

    def test_with_key_name(self) -> None:
        chunks = iter([[{"id": "P:001", "name": "Alice"}]])
        result = "".join(yaml_stream(chunks, key_name="people"))
        assert "people:" in result


class TestJsonStream:
    """Tests for json_stream function."""

    def test_basic_output(self, sample_chunks) -> None:
        result = "".join(json_stream(sample_chunks))
        # Should be valid JSON array
        assert result.strip().startswith("[")
        assert result.strip().endswith("]")
        data = json.loads(result)
        assert len(data) == 3

    def test_with_key_name(self) -> None:
        chunks = iter([[{"id": "P:001"}]])
        result = "".join(json_stream(chunks, key_name="people"))
        data = json.loads(result)
        assert "people" in data
        assert len(data["people"]) == 1


class TestJsonlStream:
    """Tests for jsonl_stream function."""

    def test_basic_output(self, sample_chunks) -> None:
        result = "".join(jsonl_stream(sample_chunks))
        lines = [line for line in result.strip().split("\n") if line]
        assert len(lines) == 3
        # Each line should be valid JSON
        for line in lines:
            obj = json.loads(line)
            assert "id" in obj

    def test_key_name_ignored(self) -> None:
        chunks = iter([[{"id": "P:001"}]])
        result = "".join(jsonl_stream(chunks, key_name="ignored"))
        # key_name should be ignored for JSONL
        obj = json.loads(result.strip())
        assert obj["id"] == "P:001"


class TestTsvStream:
    """Tests for tsv_stream function."""

    def test_basic_output(self, sample_chunks) -> None:
        result = "".join(tsv_stream(sample_chunks))
        lines = result.strip().split("\n")
        # First line should be headers
        assert "id" in lines[0]
        assert "name" in lines[0]
        assert "age" in lines[0]
        # Should have header + 3 data rows
        assert len(lines) == 4

    def test_tab_separated(self, sample_chunks) -> None:
        result = "".join(tsv_stream(sample_chunks))
        lines = result.strip().split("\n")
        # Check tabs in data rows
        assert "\t" in lines[1]

    def test_nested_objects_flattened(self, nested_chunks) -> None:
        result = "".join(tsv_stream(nested_chunks))
        # Nested keys should be flattened with __
        assert "address__street" in result or "address__city" in result


class TestCsvStream:
    """Tests for csv_stream function."""

    def test_basic_output(self) -> None:
        chunks = iter([[{"id": "P:001", "name": "Alice"}]])
        result = "".join(csv_stream(chunks))
        lines = result.strip().split("\n")
        assert "id" in lines[0]
        assert "name" in lines[0]
        assert "," in lines[0]  # CSV uses comma

    def test_comma_separated(self) -> None:
        chunks = iter([[{"id": "P:001", "name": "Alice", "age": 30}]])
        result = "".join(csv_stream(chunks))
        lines = result.strip().split("\n")
        # Should use comma separator
        assert "," in lines[1]
        assert "\t" not in lines[1]


class TestTabularStreamWriter:
    """Tests for TabularStreamWriter class."""

    def test_dynamic_headers(self) -> None:
        """Test that headers are discovered dynamically."""
        writer = TabularStreamWriter(separator="\t")
        chunks = iter(
            [
                [{"id": "P:001", "name": "Alice"}],
                [{"id": "P:002", "name": "Bob", "email": "bob@example.com"}],
            ]
        )
        result = "".join(writer.stream(chunks))
        assert writer.headers_changed is True
        assert "email" in writer.get_final_headers()

    def test_escape_value_with_separator(self) -> None:
        writer = TabularStreamWriter(separator=",")
        escaped = writer._escape_value("hello, world")
        assert escaped == '"hello, world"'

    def test_escape_value_with_quotes(self) -> None:
        writer = TabularStreamWriter()
        escaped = writer._escape_value('say "hello"')
        assert escaped == '"say ""hello"""'

    def test_escape_value_none(self) -> None:
        writer = TabularStreamWriter()
        assert writer._escape_value(None) == ""

    def test_escape_value_list(self) -> None:
        writer = TabularStreamWriter()
        escaped = writer._escape_value([1, 2, 3])
        assert escaped == "[1, 2, 3]"

    def test_escape_value_dict(self) -> None:
        writer = TabularStreamWriter()
        escaped = writer._escape_value({"key": "value"})
        assert '"key"' in escaped


class TestGetStreamWriter:
    """Tests for get_stream_writer function."""

    def test_get_yaml_writer(self) -> None:
        writer = get_stream_writer(OutputFormat.YAML)
        assert writer is yaml_stream

    def test_get_json_writer(self) -> None:
        writer = get_stream_writer(OutputFormat.JSON)
        assert writer is json_stream

    def test_get_jsonl_writer(self) -> None:
        writer = get_stream_writer(OutputFormat.JSONL)
        assert writer is jsonl_stream

    def test_get_tsv_writer(self) -> None:
        writer = get_stream_writer(OutputFormat.TSV)
        assert writer is tsv_stream

    def test_get_csv_writer(self) -> None:
        writer = get_stream_writer(OutputFormat.CSV)
        assert writer is csv_stream


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_enum_values(self) -> None:
        assert OutputFormat.YAML.value == "yaml"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.JSONL.value == "jsonl"
        assert OutputFormat.TSV.value == "tsv"
        assert OutputFormat.CSV.value == "csv"

    def test_enum_from_string(self) -> None:
        assert OutputFormat("yaml") == OutputFormat.YAML
        assert OutputFormat("jsonl") == OutputFormat.JSONL


class TestRewriteHeaderAndPad:
    """Tests for rewrite_header_and_pad function."""

    def test_basic_rewrite(self) -> None:
        from linkml_map.writers import rewrite_header_and_pad

        # Simulate a file with old headers missing a column
        original_lines = [
            "id\tname\n",
            "P:001\tAlice\n",
            "P:002\tBob\n",
        ]
        final_headers = ["id", "name", "email"]

        result = list(rewrite_header_and_pad(iter(original_lines), final_headers, "\t"))

        assert result[0] == "id\tname\temail\n"  # New header
        assert result[1] == "P:001\tAlice\t\n"  # Padded row
        assert result[2] == "P:002\tBob\t\n"  # Padded row

    def test_csv_separator(self) -> None:
        from linkml_map.writers import rewrite_header_and_pad

        original_lines = [
            "id,name\n",
            "P:001,Alice\n",
        ]
        final_headers = ["id", "name", "age"]

        result = list(rewrite_header_and_pad(iter(original_lines), final_headers, ","))

        assert result[0] == "id,name,age\n"
        assert result[1] == "P:001,Alice,\n"
