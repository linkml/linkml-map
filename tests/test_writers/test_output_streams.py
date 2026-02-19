"""Tests for output stream functions."""

import json
from pathlib import Path

import pytest
import yaml

from linkml_map.writers import (
    JSONLStreamWriter,
    JSONStreamWriter,
    MultiStreamWriter,
    OutputFormat,
    StreamWriter,
    TabularStreamWriter,
    YAMLStreamWriter,
    csv_stream,
    get_stream_writer,
    json_stream,
    jsonl_stream,
    make_stream_writer,
    tsv_stream,
    yaml_stream,
)


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
        # Should contain actual data
        assert "id: P:001" in result
        assert "name: Alice" in result

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
        # Each line should be independently valid JSON
        for line in lines:
            obj = json.loads(line)
            assert "id" in obj
            assert "name" in obj

    def test_key_name_ignored(self) -> None:
        chunks_with_key = iter([[{"id": "P:001"}]])
        chunks_without_key = iter([[{"id": "P:001"}]])
        result_with_key = "".join(jsonl_stream(chunks_with_key, key_name="ignored"))
        result_without_key = "".join(jsonl_stream(chunks_without_key))
        # key_name should have no effect on JSONL output
        assert result_with_key == result_without_key
        obj = json.loads(result_with_key.strip())
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
        assert "address__street" in result
        assert "address__city" in result


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
        # Consume the stream to trigger header discovery
        "".join(writer.stream(chunks))
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


# ---------------------------------------------------------------------------
# Tests for class-based StreamWriter hierarchy
# ---------------------------------------------------------------------------

SAMPLE_DATA = [
    {"id": "P:001", "name": "Alice", "age": 30},
    {"id": "P:002", "name": "Bob", "age": 25},
    {"id": "P:003", "name": "Charlie", "age": 35},
]


def _make_chunks(*chunk_sizes):
    """Build chunk lists from SAMPLE_DATA by splitting at given sizes."""
    result = []
    offset = 0
    for size in chunk_sizes:
        result.append(SAMPLE_DATA[offset : offset + size])
        offset += size
    return result


class TestJSONStreamWriter:
    """Tests for JSONStreamWriter class."""

    def test_single_chunk_valid_json(self) -> None:
        writer = JSONStreamWriter()
        result = "".join(writer.process(iter([SAMPLE_DATA])))
        data = json.loads(result)
        assert len(data) == 3
        assert data[0]["name"] == "Alice"

    def test_multi_chunk_comma_handling(self) -> None:
        writer = JSONStreamWriter()
        chunks = _make_chunks(2, 1)
        result = "".join(writer.process(iter(chunks)))
        data = json.loads(result)
        assert len(data) == 3

    def test_with_key_name(self) -> None:
        writer = JSONStreamWriter(key_name="people")
        result = "".join(writer.process(iter([SAMPLE_DATA[:1]])))
        data = json.loads(result)
        assert "people" in data
        assert len(data["people"]) == 1

    def test_empty_chunks(self) -> None:
        writer = JSONStreamWriter()
        result = "".join(writer.process(iter([])))
        data = json.loads(result)
        assert data == []

    def test_empty_chunk_before_data(self) -> None:
        """Empty chunks before real data should not duplicate the preamble."""
        writer = JSONStreamWriter()
        parts = list(writer.write_chunk([]))
        parts.extend(writer.write_chunk(SAMPLE_DATA[:1]))
        parts.extend(writer.finalize())
        data = json.loads("".join(parts))
        assert len(data) == 1

    def test_write_chunk_then_finalize(self) -> None:
        writer = JSONStreamWriter()
        parts = list(writer.write_chunk(SAMPLE_DATA[:2]))
        parts.extend(writer.write_chunk(SAMPLE_DATA[2:]))
        parts.extend(writer.finalize())
        data = json.loads("".join(parts))
        assert len(data) == 3


class TestJSONLStreamWriter:
    """Tests for JSONLStreamWriter class."""

    def test_one_line_per_object(self) -> None:
        writer = JSONLStreamWriter()
        result = "".join(writer.process(iter([SAMPLE_DATA])))
        lines = [l for l in result.strip().split("\n") if l]
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            assert "id" in obj

    def test_multi_chunk(self) -> None:
        writer = JSONLStreamWriter()
        chunks = _make_chunks(1, 2)
        result = "".join(writer.process(iter(chunks)))
        lines = [l for l in result.strip().split("\n") if l]
        assert len(lines) == 3

    def test_finalize_is_noop(self) -> None:
        writer = JSONLStreamWriter()
        assert list(writer.finalize()) == []


class TestYAMLStreamWriter:
    """Tests for YAMLStreamWriter class."""

    def test_basic_output(self) -> None:
        writer = YAMLStreamWriter()
        result = "".join(writer.process(iter([SAMPLE_DATA[:2]])))
        assert "---" in result
        assert "name: Alice" in result

    def test_with_key_name(self) -> None:
        writer = YAMLStreamWriter(key_name="people")
        result = "".join(writer.process(iter([SAMPLE_DATA[:1]])))
        assert "people:" in result
        parsed = yaml.safe_load(result)
        assert len(parsed["people"]) == 1

    def test_multi_chunk_with_key(self) -> None:
        writer = YAMLStreamWriter(key_name="items")
        chunks = _make_chunks(1, 2)
        result = "".join(writer.process(iter(chunks)))
        assert "items:" in result

    def test_empty_chunk_before_data_with_key(self) -> None:
        """Empty first chunk should not consume the key-name preamble."""
        writer = YAMLStreamWriter(key_name="people")
        parts = list(writer.write_chunk([]))
        parts.extend(writer.write_chunk(SAMPLE_DATA[:1]))
        parts.extend(writer.finalize())
        result = "".join(parts)
        assert "people:" in result
        parsed = yaml.safe_load(result)
        assert len(parsed["people"]) == 1


class TestTabularStreamWriterChunk:
    """Tests for TabularStreamWriter chunk-based API."""

    def test_write_chunk_produces_header_and_rows(self) -> None:
        writer = TabularStreamWriter(separator="\t")
        output = list(writer.write_chunk(SAMPLE_DATA[:2]))
        output.extend(writer.finalize())
        text = "".join(output)
        lines = text.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        assert "id" in lines[0]
        assert "name" in lines[0]

    def test_process_matches_stream(self) -> None:
        writer_a = TabularStreamWriter(separator="\t")
        writer_b = TabularStreamWriter(separator="\t")
        chunks = [SAMPLE_DATA[:2], SAMPLE_DATA[2:]]
        result_process = "".join(writer_a.process(iter(chunks)))
        result_stream = "".join(writer_b.stream(iter([SAMPLE_DATA[:2], SAMPLE_DATA[2:]])))
        assert result_process == result_stream

    def test_headers_tracked_across_chunks(self) -> None:
        writer = TabularStreamWriter(separator="\t")
        list(writer.write_chunk([{"id": "1", "name": "A"}]))
        list(writer.write_chunk([{"id": "2", "name": "B", "email": "b@example.com"}]))
        list(writer.finalize())
        assert writer.headers_changed is True
        assert "email" in writer.get_final_headers()

    def test_is_stream_writer_subclass(self) -> None:
        assert issubclass(TabularStreamWriter, StreamWriter)


class TestMakeStreamWriter:
    """Tests for make_stream_writer factory."""

    @pytest.mark.parametrize(
        "fmt, expected_type",
        [
            (OutputFormat.JSON, JSONStreamWriter),
            (OutputFormat.JSONL, JSONLStreamWriter),
            (OutputFormat.YAML, YAMLStreamWriter),
            (OutputFormat.TSV, TabularStreamWriter),
            (OutputFormat.CSV, TabularStreamWriter),
        ],
    )
    def test_returns_correct_type(self, fmt, expected_type) -> None:
        writer = make_stream_writer(fmt)
        assert isinstance(writer, expected_type)

    def test_json_key_name_passed(self) -> None:
        writer = make_stream_writer(OutputFormat.JSON, key_name="items")
        assert isinstance(writer, JSONStreamWriter)
        assert writer.key_name == "items"

    def test_tsv_separator(self) -> None:
        writer = make_stream_writer(OutputFormat.TSV)
        assert isinstance(writer, TabularStreamWriter)
        assert writer.separator == "\t"

    def test_csv_separator(self) -> None:
        writer = make_stream_writer(OutputFormat.CSV)
        assert isinstance(writer, TabularStreamWriter)
        assert writer.separator == ","


class TestMultiStreamWriter:
    """Tests for MultiStreamWriter fan-out."""

    def test_writes_multiple_formats(self, tmp_path: Path) -> None:
        json_path = tmp_path / "out.json"
        jsonl_path = tmp_path / "out.jsonl"
        tsv_path = tmp_path / "out.tsv"

        outputs = [
            (JSONStreamWriter(), json_path),
            (JSONLStreamWriter(), jsonl_path),
            (TabularStreamWriter(separator="\t"), tsv_path),
        ]
        multi = MultiStreamWriter(outputs)
        multi.write_all(iter([SAMPLE_DATA]))

        # Verify JSON
        json_data = json.loads(json_path.read_text())
        assert len(json_data) == 3
        assert json_data[0]["name"] == "Alice"

        # Verify JSONL
        jsonl_lines = [l for l in jsonl_path.read_text().strip().split("\n") if l]
        assert len(jsonl_lines) == 3
        assert json.loads(jsonl_lines[1])["name"] == "Bob"

        # Verify TSV
        tsv_lines = tsv_path.read_text().strip().split("\n")
        assert len(tsv_lines) == 4  # header + 3 rows
        assert "id" in tsv_lines[0]

    def test_multi_chunk_fanout(self, tmp_path: Path) -> None:
        json_path = tmp_path / "out.json"
        jsonl_path = tmp_path / "out.jsonl"

        outputs = [
            (JSONStreamWriter(), json_path),
            (JSONLStreamWriter(), jsonl_path),
        ]
        multi = MultiStreamWriter(outputs)
        chunks = _make_chunks(2, 1)
        multi.write_all(iter(chunks))

        json_data = json.loads(json_path.read_text())
        assert len(json_data) == 3

        jsonl_lines = [l for l in jsonl_path.read_text().strip().split("\n") if l]
        assert len(jsonl_lines) == 3

    def test_tabular_header_rewrite(self, tmp_path: Path) -> None:
        """Test that MultiStreamWriter rewrites headers when they change."""
        tsv_path = tmp_path / "out.tsv"

        writer = TabularStreamWriter(separator="\t")
        multi = MultiStreamWriter([(writer, tsv_path)])

        # First chunk has 2 fields, second adds a third
        chunk1 = [{"id": "1", "name": "A"}]
        chunk2 = [{"id": "2", "name": "B", "email": "b@x.com"}]
        multi.write_all(iter([chunk1, chunk2]))

        content = tsv_path.read_text()
        lines = content.strip().split("\n")
        # After rewrite, header should include all three columns
        assert "email" in lines[0]
        # All data rows should have 3 fields
        for line in lines[1:]:
            assert len(line.split("\t")) == 3
