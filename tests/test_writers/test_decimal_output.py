"""Decimals round-trip exactly through every output format (#353).

Each format is written through the normal writer path and read back with a reader
that parses numbers as :class:`~decimal.Decimal`, so any rounding through a float
shows up as a mismatch.
"""

import csv
import io
import json
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest
import yaml

from linkml_map.cli.cli import dump_output
from linkml_map.writers.output_streams import MultiStreamWriter, OutputFormat, make_stream_writer

PRECISE = Decimal("0.123456789012345678901")

ROWS = [
    {"id": "a", "v": Decimal("52.30"), "q": {"unit": "mg", "val": PRECISE}, "vs": [Decimal("1"), Decimal("2.5")]},
    {"id": "b", "v": Decimal("7"), "q": {"unit": "g", "val": Decimal("1E-7")}, "vs": [Decimal("-3.25")]},
]


class _DecimalLoader(yaml.SafeLoader):
    """Reads YAML floats as decimals, so the test sees the digits actually written."""


_DecimalLoader.add_constructor("tag:yaml.org,2002:float", lambda loader, node: Decimal(loader.construct_scalar(node)))


def _write(fmt: OutputFormat, target: Path) -> None:
    MultiStreamWriter([(make_stream_writer(fmt), target)]).write_all(iter([ROWS]))


def _read_json(text: str) -> list[dict]:
    return json.loads(text, parse_float=Decimal)


def _read_jsonl(text: str) -> list[dict]:
    return [json.loads(line, parse_float=Decimal) for line in text.splitlines()]


def _read_yaml(text: str) -> list[dict]:
    return [doc for doc in yaml.load_all(text, Loader=_DecimalLoader) if doc is not None]


def _read_tabular(text: str, separator: str) -> list[dict]:
    rows = csv.DictReader(io.StringIO(text), delimiter=separator)
    return [
        {
            "id": r["id"],
            "v": Decimal(r["v"]),
            "q": {"unit": r["q__unit"], "val": Decimal(r["q__val"])},
            "vs": json.loads(r["vs"], parse_float=Decimal, parse_int=Decimal),
        }
        for r in rows
    ]


@pytest.mark.parametrize(
    ("fmt", "read"),
    [
        (OutputFormat.JSON, _read_json),
        (OutputFormat.JSONL, _read_jsonl),
        (OutputFormat.YAML, _read_yaml),
        (OutputFormat.TSV, lambda text: _read_tabular(text, "\t")),
        (OutputFormat.CSV, lambda text: _read_tabular(text, ",")),
    ],
)
def test_text_formats_round_trip_decimals(tmp_path: Path, fmt: OutputFormat, read) -> None:
    """Text output holds every digit, including trailing zeros."""
    target = tmp_path / f"out.{fmt.value}"
    _write(fmt, target)
    text = target.read_text()
    assert read(text) == ROWS
    assert "52.30" in text
    assert "0.123456789012345678901" in text


@pytest.mark.parametrize("fmt", [OutputFormat.PARQUET, OutputFormat.DUCKDB])
def test_columnar_formats_store_exact_decimal_columns(tmp_path: Path, fmt: OutputFormat) -> None:
    """Decimals become DECIMAL columns sized to the data, at the top level and nested."""
    target = tmp_path / f"out.{fmt.value}"
    _write(fmt, target)
    con = duckdb.connect(str(target)) if fmt == OutputFormat.DUCKDB else duckdb.connect()
    source = "out" if fmt == OutputFormat.DUCKDB else f"read_parquet('{target}')"

    types = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {source}").fetchall()}
    assert types["v"] == "DECIMAL(4,2)"
    assert types["q"] == "STRUCT(unit VARCHAR, val DECIMAL(21,21))"
    assert types["vs"] == "DECIMAL(3,2)[]"

    rows = con.execute(f"SELECT id, v, q.val, vs FROM {source} ORDER BY id").fetchall()
    assert rows == [
        ("a", Decimal("52.30"), PRECISE, [Decimal("1"), Decimal("2.5")]),
        ("b", Decimal("7"), Decimal("1E-7"), [Decimal("-3.25")]),
    ]


def test_columnar_rejects_decimals_wider_than_duckdb_supports(tmp_path: Path) -> None:
    """A decimal needing more than 38 digits fails loudly rather than rounding."""
    target = tmp_path / "out.parquet"
    writer = make_stream_writer(OutputFormat.PARQUET)
    rows = [{"q": {"val": Decimal("1" * 20 + "." + "1" * 19)}}]
    with pytest.raises(ValueError, match=r"q\.val need 39 digits"):
        MultiStreamWriter([(writer, target)]).write_all(iter([rows]))


@pytest.mark.parametrize(
    ("output_format", "read"),
    [("json", _read_json), ("jsonl", _read_jsonl), ("yaml", _read_yaml)],
)
def test_single_object_output_round_trips_decimals(tmp_path: Path, output_format: str, read) -> None:
    """The CLI's non-streaming output path keeps decimals exact too."""
    target = tmp_path / f"out.{output_format}"
    dump_output(ROWS, output_format, str(target))
    parsed = read(target.read_text())
    assert (parsed[0] if output_format == "yaml" else parsed) == ROWS
