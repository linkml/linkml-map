"""Streaming output writers for linkml-map transformations."""

import json
import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import IO, Any, Optional, Union

import yaml
from flatten_dict import flatten
from flatten_dict.reducers import make_reducer

logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Supported output formats for streaming."""

    YAML = "yaml"
    JSON = "json"
    JSONL = "jsonl"
    TSV = "tsv"
    CSV = "csv"


class StreamWriter(ABC):
    """
    Abstract base class for chunk-based stream writers.

    Each writer converts individual chunks of objects into formatted string
    fragments. The ``process`` method drives the full lifecycle: it iterates
    over chunks, calling ``write_chunk`` for each, then ``finalize`` at the
    end.

    Subclasses must implement ``write_chunk`` and ``finalize``.
    """

    @abstractmethod
    def write_chunk(self, chunk: list[dict]) -> Iterator[str]:
        """
        Emit formatted string fragments for a single chunk of objects.

        :param chunk: A list of dictionaries (one chunk of transformed data).
        :yield: Formatted string fragments.
        """

    @abstractmethod
    def finalize(self) -> Iterator[str]:
        """
        Emit any trailing content after all chunks have been processed.

        :yield: Trailing string fragments (may be empty).
        """

    def process(self, chunks: Iterator[list[dict]]) -> Iterator[str]:
        """
        Drive the full streaming lifecycle over an iterator of chunks.

        :param chunks: Iterator of lists of dictionaries.
        :yield: Formatted string fragments for the entire stream.
        """
        for chunk in chunks:
            yield from self.write_chunk(chunk)
        yield from self.finalize()


class JSONStreamWriter(StreamWriter):
    """
    Class-based streaming writer for JSON array output.

    Emits a JSON array (optionally wrapped under a key) incrementally,
    handling comma placement between objects.

    :param key_name: Optional key to wrap the array, e.g. ``{"people": [...]}``.
    """

    def __init__(self, key_name: Optional[str] = None) -> None:
        """Initialize with an optional wrapping key name."""
        self.key_name = key_name
        self._started = False
        self._first_object = True

    def _emit_preamble(self) -> Iterator[str]:
        """Emit the opening bracket(s) exactly once."""
        if not self._started:
            self._started = True
            if self.key_name:
                yield f"{{{json.dumps(self.key_name)}: [\n"
            else:
                yield "[\n"

    def write_chunk(self, chunk: list[dict]) -> Iterator[str]:
        """
        Emit JSON fragments for each object in the chunk.

        :param chunk: A list of dictionaries.
        :yield: JSON string fragments.
        """
        yield from self._emit_preamble()

        for obj in chunk:
            prefix = "" if self._first_object else ",\n"
            self._first_object = False
            yield prefix + json.dumps(obj, ensure_ascii=False, indent=2)

    def finalize(self) -> Iterator[str]:
        """
        Emit the closing bracket(s) for the JSON structure.

        :yield: Closing JSON fragments.
        """
        yield from self._emit_preamble()

        if self.key_name:
            yield "\n]}\n"
        else:
            yield "\n]\n"


class JSONLStreamWriter(StreamWriter):
    """
    Class-based streaming writer for JSON Lines output.

    Each object is emitted as a single line of JSON. Stateless—no preamble
    or postamble is needed.
    """

    def write_chunk(self, chunk: list[dict]) -> Iterator[str]:
        """
        Emit one JSON line per object.

        :param chunk: A list of dictionaries.
        :yield: JSONL string lines.
        """
        for obj in chunk:
            yield json.dumps(obj, ensure_ascii=False) + "\n"

    def finalize(self) -> Iterator[str]:
        """
        No trailing content needed for JSONL.

        :yield: Nothing.
        """
        return iter(())


class YAMLStreamWriter(StreamWriter):
    """
    Class-based streaming writer for YAML output.

    If ``key_name`` is provided, wraps all objects under that key as a list.
    Otherwise, outputs each object as a separate YAML document.

    :param key_name: Optional key to wrap all objects.
    """

    def __init__(self, key_name: Optional[str] = None) -> None:
        """Initialize with an optional wrapping key name."""
        self.key_name = key_name
        self._first_chunk = True

    def write_chunk(self, chunk: list[dict]) -> Iterator[str]:
        """
        Emit YAML fragments for a chunk.

        Empty chunks are skipped to avoid emitting an empty-list preamble
        that would break subsequent continuation chunks.

        :param chunk: A list of dictionaries.
        :yield: YAML string fragments.
        """
        if not chunk:
            return

        if self.key_name:
            yaml_str = yaml.dump(
                {self.key_name: chunk}, default_flow_style=False, allow_unicode=True
            )
            if self._first_chunk:
                yield yaml_str
                self._first_chunk = False
            else:
                lines = yaml_str.splitlines()
                yield "\n".join(lines[1:]) + "\n"
        else:
            for obj in chunk:
                yield yaml.dump(obj, default_flow_style=False, allow_unicode=True)
                yield "---\n"

    def finalize(self) -> Iterator[str]:
        """
        No trailing content needed for YAML.

        :yield: Nothing.
        """
        return iter(())


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


class TabularStreamWriter(StreamWriter):
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

    def write_chunk(self, chunk: list[dict]) -> Iterator[str]:
        """
        Emit tabular rows for a single chunk of objects.

        :param chunk: A list of dictionaries.
        :yield: TSV/CSV formatted strings.
        """
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

    def finalize(self) -> Iterator[str]:
        """
        Track header changes after all chunks processed.

        :yield: Nothing (side-effect only).
        """
        if self.headers != self.initial_headers:
            self._headers_changed = True
        return iter(())

    def stream(
        self,
        chunks: Iterator[list[dict[str, Any]]],
        key_name: Optional[str] = None,  # noqa: ARG002
    ) -> Iterator[str]:
        """
        Stream objects as tabular data. Backward-compatible alias for ``process``.

        :param chunks: Iterator of lists of dictionaries
        :param key_name: Unused, kept for API consistency
        :yield: TSV/CSV formatted strings
        """
        yield from self.process(chunks)

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


# Extension-to-format mapping used by make_stream_writer and CLI
EXTENSION_FORMAT_MAP = {
    ".yaml": OutputFormat.YAML,
    ".yml": OutputFormat.YAML,
    ".json": OutputFormat.JSON,
    ".jsonl": OutputFormat.JSONL,
    ".tsv": OutputFormat.TSV,
    ".csv": OutputFormat.CSV,
}


def make_stream_writer(
    output_format: OutputFormat,
    key_name: Optional[str] = None,
    separator: Optional[str] = None,
) -> StreamWriter:
    """
    Return the appropriate ``StreamWriter`` for a format.

    :param output_format: The desired output format.
    :param key_name: Optional key for formats that support wrapping (JSON, YAML).
    :param separator: Optional separator override for tabular formats.
    :return: A ``StreamWriter`` instance.
    :raises ValueError: If the format is not supported.
    """
    if output_format == OutputFormat.JSON:
        return JSONStreamWriter(key_name=key_name)
    if output_format == OutputFormat.JSONL:
        return JSONLStreamWriter()
    if output_format == OutputFormat.YAML:
        return YAMLStreamWriter(key_name=key_name)
    if output_format == OutputFormat.TSV:
        return TabularStreamWriter(separator=separator or "\t")
    if output_format == OutputFormat.CSV:
        return TabularStreamWriter(separator=separator or ",")
    msg = f"No stream writer available for format: {output_format}"
    raise ValueError(msg)


class MultiStreamWriter:
    """
    Fan-out writer that sends the same chunks to multiple ``StreamWriter`` instances.

    Each output is a ``(StreamWriter, target)`` pair where *target* is either a
    ``Path`` (opened and closed internally, eligible for header rewrite) or an
    open file handle such as ``sys.stdout`` (written to directly, never closed
    or rewritten by this class).

    :param outputs: List of ``(StreamWriter, target)`` tuples.
    """

    def __init__(self, outputs: list[tuple[StreamWriter, Union[Path, IO[str]]]]) -> None:
        """Initialize with a list of (writer, target) output pairs."""
        self.outputs = outputs

    def write_all(self, chunks: Iterator[list[dict]]) -> None:
        """
        Consume *chunks* once and write to all outputs simultaneously.

        :param chunks: Iterator of lists of dictionaries.
        """
        handles: list[IO[str]] = []
        owned: list[bool] = []  # True when we opened the handle (so we close it)
        try:
            for _writer, target in self.outputs:
                if isinstance(target, Path):
                    fh = open(target, "w", encoding="utf-8")  # noqa: SIM115
                    handles.append(fh)
                    owned.append(True)
                else:
                    handles.append(target)
                    owned.append(False)

            # Fan out each chunk to every writer
            for chunk in chunks:
                for idx, (writer, _target) in enumerate(self.outputs):
                    for fragment in writer.write_chunk(chunk):
                        handles[idx].write(fragment)

            # Finalize each writer
            for idx, (writer, _target) in enumerate(self.outputs):
                for fragment in writer.finalize():
                    handles[idx].write(fragment)

        finally:
            for fh, is_owned in zip(handles, owned):  # noqa: B905
                if is_owned:
                    fh.close()

        # Post-process tabular Path outputs that had header changes
        for writer, target in self.outputs:
            if (
                isinstance(target, Path)
                and isinstance(writer, TabularStreamWriter)
                and writer.headers_changed
            ):
                logger.info("Rewriting %s with updated headers", target)
                tmp_path = str(target) + ".tmp"
                with open(target, encoding="utf-8") as src, open(tmp_path, "w", encoding="utf-8") as dst:
                    for line in rewrite_header_and_pad(
                        iter(src), writer.get_final_headers(), writer.separator
                    ):
                        dst.write(line)
                os.replace(tmp_path, str(target))
