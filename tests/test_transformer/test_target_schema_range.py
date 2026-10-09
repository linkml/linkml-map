"""Datatype coercion falls back to the target schema's slot range (#356).

When a slot derivation declares no ``range``, the target schema owns the type:
tabular strings are coerced to it, and an explicit spec range still wins.
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
    id: https://example.org/range-source
    name: range_source
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: range_source
    default_range: string
    imports: [linkml:types]
    classes:
      Row:
        attributes:
          id: {identifier: true}
          count: {}
          ratio: {}
          amount: {}
          flag: {}
          score: {}
          color: {}
          site: {}
          note: {}
          counts: {multivalued: true}
""")

TARGET_SCHEMA = textwrap.dedent("""\
    id: https://example.org/range-target
    name: range_target
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: range_target
    default_range: string
    imports: [linkml:types]
    types:
      Score:
        typeof: decimal
    enums:
      Color:
        permissible_values:
          red: {}
    classes:
      Site:
        attributes:
          id: {identifier: true}
      Measurement:
        attributes:
          id: {identifier: true}
          count: {range: integer}
          ratio: {range: float}
          ratio_text: {range: float}
          amount: {range: decimal}
          flag: {range: boolean}
          score: {range: Score}
          color: {range: Color}
          site: {range: Site}
          note: {}
          counts: {range: integer, multivalued: true}
""")

SPEC = textwrap.dedent("""\
    id: target-schema-range
    class_derivations:
      Measurement:
        populated_from: Row
        slot_derivations:
          id:
            populated_from: id
          count:
            populated_from: count
          ratio:
            populated_from: ratio
          ratio_text:
            populated_from: ratio
            range: string
          amount:
            populated_from: amount
          flag:
            populated_from: flag
          score:
            populated_from: score
          color:
            populated_from: color
          site:
            populated_from: site
          note:
            populated_from: note
          counts:
            populated_from: counts
""")

ROW = {
    "id": "r1",
    "count": "7",
    "ratio": "1.5",
    "amount": "52.30",
    "flag": "false",
    "score": "0.10",
    "color": "red",
    "site": "S1",
    "note": 42,
    "counts": ["1", "2"],
}


def _transformer(*, with_target: bool = True) -> ObjectTransformer:
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    if with_target:
        tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(yaml.safe_load(SPEC))
    return tr


def test_values_take_the_target_schema_range() -> None:
    """Each built-in range, custom typeof chain, and multivalued slot is coerced."""
    out = _transformer().map_object(ROW, "Row")
    assert out["count"] == 7
    assert out["ratio"] == 1.5
    assert out["amount"] == Decimal("52.30")
    assert out["flag"] is False
    assert out["score"] == Decimal("0.10")
    assert out["note"] == "42"
    assert out["counts"] == [1, 2]


def test_spec_range_overrides_target_schema() -> None:
    """An explicit range on the derivation wins over the target slot's range."""
    out = _transformer().map_object(ROW, "Row")
    assert out["ratio_text"] == "1.5"


def test_class_and_enum_ranges_pass_through() -> None:
    """Class- and enum-ranged slots have no datatype to coerce to."""
    out = _transformer().map_object(ROW, "Row")
    assert out["color"] == "red"
    assert out["site"] == "S1"


def test_no_target_schema_leaves_values_alone() -> None:
    """Without a target schema, only spec ranges coerce."""
    out = _transformer(with_target=False).map_object(ROW, "Row")
    assert out["count"] == "7"
    assert out["flag"] == "false"
    assert out["note"] == 42
    assert out["ratio_text"] == "1.5"


@pytest.mark.parametrize(
    ("source", "expected"),
    [("true", True), ("FALSE", False), ("1", True), ("0", False), (True, True), (0, False)],
)
def test_boolean_strings_are_parsed(source: str | bool | int, expected: bool) -> None:
    """Boolean strings parse by value; ``"false"`` is not truthy."""
    out = _transformer().map_object({"id": "r1", "flag": source}, "Row")
    assert out["flag"] is expected


def test_unparseable_boolean_fails() -> None:
    """A string that is not a boolean fails loudly instead of becoming ``True``."""
    with pytest.raises(TransformationError, match="to boolean"):
        _transformer().map_object({"id": "r1", "flag": "maybe"}, "Row")


def test_map_data_coerces_tsv_with_target_schema(tmp_path: Path) -> None:
    """TSV in with ``--target-schema``: the spec needs no range for exact decimals."""
    (tmp_path / "source.yaml").write_text(SOURCE_SCHEMA)
    (tmp_path / "target.yaml").write_text(TARGET_SCHEMA)
    (tmp_path / "spec.yaml").write_text(SPEC)
    (tmp_path / "Row.tsv").write_text("id\tamount\tflag\nr1\t52.30\tfalse\n")
    output = tmp_path / "out.json"

    result = CliRunner().invoke(
        main,
        [
            "map-data",
            "-T",
            str(tmp_path / "spec.yaml"),
            "-s",
            str(tmp_path / "source.yaml"),
            "--target-schema",
            str(tmp_path / "target.yaml"),
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
    assert [(r["id"], str(r["amount"]), r["flag"]) for r in rows] == [("r1", "52.30", False)]
