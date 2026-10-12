"""Coercion of slot derivations with ``range: decimal`` (#353).

Tabular sources deliver every value as a string; a ``decimal`` range must turn it
into an exact :class:`~decimal.Decimal`, never a float.
"""

import json
import textwrap
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from linkml_runtime import SchemaView

from linkml_map.cli.cli import main
from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/decimal-source
    name: decimal_source
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: decimal_source
    default_range: string
    imports: [linkml:types]
    classes:
      Row:
        attributes:
          id: {identifier: true}
          value: {}
          values: {multivalued: true}
""")

SPEC = textwrap.dedent("""\
    id: decimal-range
    class_derivations:
      Measurement:
        populated_from: Row
        slot_derivations:
          id:
            populated_from: id
          value_decimal:
            populated_from: value
            range: decimal
          values_decimal:
            populated_from: values
            range: decimal
""")


def _transformer() -> ObjectTransformer:
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.create_transformer_specification(yaml.safe_load(SPEC))
    return tr


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("52.3", "52.3"),
        ("52.30", "52.30"),
        ("52", "52"),
        ("-0.05", "-0.05"),
        ("0.123456789012345678901", "0.123456789012345678901"),
        (0.1, "0.1"),
        (7, "7"),
    ],
)
def test_decimal_range_coerces_exactly(source: str | float | int, expected: str) -> None:
    """The value becomes a Decimal with exactly the source's digits."""
    out = _transformer().map_object({"id": "r1", "value": source}, "Row")
    assert isinstance(out["value_decimal"], Decimal)
    assert str(out["value_decimal"]) == expected


def test_decimal_range_coerces_each_item() -> None:
    """A multivalued slot coerces every item."""
    out = _transformer().map_object({"id": "r1", "values": ["1", "2.50"]}, "Row")
    assert out["values_decimal"] == [Decimal("1"), Decimal("2.50")]
    assert [str(v) for v in out["values_decimal"]] == ["1", "2.50"]


@pytest.mark.parametrize("source", ["abc", "NaN", "Infinity", True])
def test_decimal_range_rejects_non_numbers(source: str | bool) -> None:
    """A value with no exact decimal reading fails loudly instead of passing through."""
    with pytest.raises(TransformationError, match="to decimal"):
        _transformer().map_object({"id": "r1", "value": source}, "Row")


def test_map_data_writes_exact_json_numbers(tmp_path: Path) -> None:
    """TSV in, JSON out: the decimal is a JSON number with every digit intact."""
    (tmp_path / "schema.yaml").write_text(SOURCE_SCHEMA)
    (tmp_path / "spec.yaml").write_text(SPEC)
    (tmp_path / "Row.tsv").write_text("id\tvalue\nr1\t52.30\nr2\t0.123456789012345678901\n")
    output = tmp_path / "out.json"

    result = CliRunner().invoke(
        main,
        [
            "map-data",
            "-T",
            str(tmp_path / "spec.yaml"),
            "-s",
            str(tmp_path / "schema.yaml"),
            "--source-type",
            "Row",
            "-f",
            "json",
            "-o",
            str(output),
            str(tmp_path / "Row.tsv"),
        ],
    )
    assert result.exit_code == 0, result.output

    rows = json.loads(output.read_text(), parse_float=Decimal)
    assert [(r["id"], str(r["value_decimal"])) for r in rows] == [("r1", "52.30"), ("r2", "0.123456789012345678901")]
