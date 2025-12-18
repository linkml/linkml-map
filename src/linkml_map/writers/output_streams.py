"""Streaming output writers for linkml-map transformations."""

import json
from collections.abc import Iterator
from enum import Enum
from typing import Any, Optional

import yaml
from flatten_dict import flatten
from flatten_dict.reducers import make_reducer


class OutputFormat(str, Enum):
    """Supported output formats for streaming."""

    YAML = "yaml"
    JSON = "json"
    JSONL = "jsonl"
    TSV = "tsv"
    CSV = "csv"


def yaml_stream(
    chunks: Iterator[list[dict[str, Any]]],
    key_name: Optional[str] = None,
) -> Iterator[str]:
    """
    Convert chunks of objects to YAML format.

    If key_name is provided, wraps all objects under that key as a list.
    Otherwise, outputs each object as a separate YAML document.

    :param chunks: Iterator of lists of dictionaries
    :param key_name: Optional key name to wrap all objects
    :yield: YAML formatted strings
    """
    if key_name:
        first_chunk = True
        for chunk in chunks:
            yaml_str = yaml.dump({key_name: chunk}, default_flow_style=False, allow_unicode=True)
            if first_chunk:
                yield yaml_str
                first_chunk = False
            else:
                # Remove the key line and adjust indentation for continuation
                lines = yaml_str.splitlines()
                yield "\n".join(lines[1:]) + "\n"
    else:
        for chunk in chunks:
            for obj in chunk:
                yield yaml.dump(obj, default_flow_style=False, allow_unicode=True)
                yield "---\n"


def json_stream(
    chunks: Iterator[list[dict[str, Any]]],
    key_name: Optional[str] = None,
) -> Iterator[str]:
    """
    Convert chunks of objects to JSON format.

    Outputs a single JSON object/array containing all transformed data.

    :param chunks: Iterator of lists of dictionaries
    :param key_name: Optional key name to wrap all objects
    :yield: JSON formatted strings
    """
    first_chunk = True
    if key_name:
        yield f"{{{json.dumps(key_name)}: [\n"
    else:
        yield "[\n"

    for chunk in chunks:
        for obj in chunk:
            prefix = "" if first_chunk else ",\n"
            first_chunk = False
            yield prefix + json.dumps(obj, ensure_ascii=False, indent=2)

    if key_name:
        yield "\n]}\n"
    else:
        yield "\n]\n"


def jsonl_stream(
    chunks: Iterator[list[dict[str, Any]]],
    key_name: Optional[str] = None,  # noqa: ARG001
) -> Iterator[str]:
    """
    Convert chunks of objects to JSON Lines format.

    Each object is written as a single line of JSON.

    :param chunks: Iterator of lists of dictionaries
    :param key_name: Unused, kept for API consistency
    :yield: JSONL formatted strings (one JSON object per line)
    """
    for chunk in chunks:
        for obj in chunk:
            yield json.dumps(obj, ensure_ascii=False) + "\n"


class TabularStreamWriter:
    """
    Streaming writer for TSV/CSV output with dynamic header handling.

    This class handles the complexity of writing tabular data when:
    - Headers may not be known until data is processed
    - Headers may expand as new columns are discovered
    - Nested objects need to be flattened
    """

    def __init__(
        self,
        separator: str = "\t",
        reducer_str: str = "__",
    ) -> None:
        """
        Initialize the tabular stream writer.

        :param separator: Column separator (tab for TSV, comma for CSV)
        :param reducer_str: String used to join nested keys when flattening
        """
        self.separator = separator
        self.reducer = make_reducer(reducer_str)
        self.headers: list[str] = []
        self.initial_headers: list[str] = []
        self._headers_changed = False

    def stream(
        self,
        chunks: Iterator[list[dict[str, Any]]],
        key_name: Optional[str] = None,  # noqa: ARG002
    ) -> Iterator[str]:
        """
        Stream objects as tabular data.

        :param chunks: Iterator of lists of dictionaries
        :param key_name: Unused, kept for API consistency
        :yield: TSV/CSV formatted strings
        """
        for chunk in chunks:
            for obj in chunk:
                flat = flatten(obj, reducer=self.reducer)

                # Track new headers
                for k in flat:
                    if k not in self.headers:
                        self.headers.append(k)

                # Emit header row on first object
                if len(self.initial_headers) == 0:
                    self.initial_headers = list(self.headers)
                    yield self.separator.join(self.headers) + "\n"

                # Emit data row
                row = self.separator.join(
                    self._escape_value(flat.get(h, "")) for h in self.headers
                )
                yield row + "\n"

        # Track if headers changed during streaming
        if self.headers != self.initial_headers:
            self._headers_changed = True

    def _escape_value(self, value: Any) -> str:
        """
        Escape a value for tabular output.

        Handles None, lists, dicts, and values containing separators.
        """
        if value is None:
            return ""
        if isinstance(value, (list, dict)):
            # Serialize complex values as JSON
            return json.dumps(value, ensure_ascii=False)
        str_value = str(value)
        # Quote values containing separator, quotes, or newlines
        if self.separator in str_value or '"' in str_value or "\n" in str_value:
            return '"' + str_value.replace('"', '""') + '"'
        return str_value

    @property
    def headers_changed(self) -> bool:
        """
        Check if headers changed during streaming.

        If True, the output file may need to be rewritten with the full headers.
        """
        return self._headers_changed

    def get_final_headers(self) -> list[str]:
        """Get the final set of headers after streaming."""
        return list(self.headers)


def tsv_stream(
    chunks: Iterator[list[dict[str, Any]]],
    key_name: Optional[str] = None,
) -> Iterator[str]:
    """
    Convert chunks of objects to TSV format.

    :param chunks: Iterator of lists of dictionaries
    :param key_name: Unused, kept for API consistency
    :yield: TSV formatted strings
    """
    writer = TabularStreamWriter(separator="\t")
    yield from writer.stream(chunks, key_name)

    # Store headers on the function for post-processing if needed
    if writer.headers_changed:
        tsv_stream.headers = writer.get_final_headers()  # type: ignore[attr-defined]


def csv_stream(
    chunks: Iterator[list[dict[str, Any]]],
    key_name: Optional[str] = None,
) -> Iterator[str]:
    """
    Convert chunks of objects to CSV format.

    :param chunks: Iterator of lists of dictionaries
    :param key_name: Unused, kept for API consistency
    :yield: CSV formatted strings
    """
    writer = TabularStreamWriter(separator=",")
    yield from writer.stream(chunks, key_name)

    # Store headers on the function for post-processing if needed
    if writer.headers_changed:
        csv_stream.headers = writer.get_final_headers()  # type: ignore[attr-defined]


def rewrite_header_and_pad(
    lines: Iterator[str],
    final_headers: list[str],
    separator: str = "\t",
    chunk_size: int = 1000,
) -> Iterator[str]:
    """
    Rewrite a tabular file with updated headers and padded rows.

    Use this when headers changed during initial streaming and the
    output file needs to be corrected.

    :param lines: Iterator of lines from the original file
    :param final_headers: The complete set of headers
    :param separator: Column separator
    :param chunk_size: Number of lines to process at once
    :yield: Corrected lines with proper headers and padding
    """
    from more_itertools import chunked

    header_count = len(final_headers)
    header_line = separator.join(final_headers) + "\n"

    def pad_line(line: str) -> str:
        """Pad a single line to match header count."""
        fields = line.rstrip("\n").split(separator)
        if len(fields) < header_count:
            fields.extend([""] * (header_count - len(fields)))
        return separator.join(fields) + "\n"

    # Yield new header
    yield header_line

    # Skip original header and pad remaining lines
    lines_iter = iter(lines)
    next(lines_iter, None)  # Skip original header

    for chunk in chunked(lines_iter, chunk_size):
        for line in chunk:
            yield pad_line(line)


def get_stream_writer(output_format: OutputFormat) -> Any:
    """
    Get the appropriate stream writer for the given format.

    :param output_format: The desired output format
    :return: Stream writer function
    """
    writers = {
        OutputFormat.YAML: yaml_stream,
        OutputFormat.JSON: json_stream,
        OutputFormat.JSONL: jsonl_stream,
        OutputFormat.TSV: tsv_stream,
        OutputFormat.CSV: csv_stream,
    }
    writer = writers.get(output_format)
    if writer is None:
        msg = f"No stream writer available for format: {output_format}"
        raise ValueError(msg)
    return writer
