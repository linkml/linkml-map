"""``value_if_missing`` and ``value_if_unmapped`` fill a populated_from slot that would come out null."""

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map import ObjectTransformer
from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec

SOURCE = """\
id: https://example.org/s
name: s
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string
classes:
  answers:
    attributes:
      pid:
        identifier: true
      status:
        range: integer
      years:
        range: integer
"""

TARGET = """\
id: https://example.org/t
name: t
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string
classes:
  Condition:
    attributes:
      pid:
        identifier: true
      status:
        range: StatusEnum
      years:
        range: integer
enums:
  StatusEnum:
    permissible_values:
      PRESENT:
      ABSENT:
      UNKNOWN:
        meaning: OMOP:45877986
"""


def _transformer(status: dict, years: dict | None = None) -> ObjectTransformer:
    slots = {"pid": {"populated_from": "pid"}, "status": {"populated_from": "status", **status}}
    if years:
        slots["years"] = {"populated_from": "years", **years}
    spec = {"class_derivations": {"Condition": {"populated_from": "answers", "slot_derivations": slots}}}
    return ObjectTransformer(
        specification=yaml.safe_load(yaml.dump(spec)),
        source_schemaview=SchemaView(SOURCE),
        target_schemaview=SchemaView(TARGET),
    )


MAPPED = {"value_mappings": {"0": "ABSENT", "1": "PRESENT"}}


def _status(tr: ObjectTransformer, row: dict):
    return tr.map_object(row, source_type="answers").get("status")


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"pid": "P1", "status": 1}, "PRESENT"),
        ({"pid": "P2", "status": None}, "UNKNOWN"),
        ({"pid": "P3"}, "UNKNOWN"),
        ({"pid": "P4", "status": 9}, None),
    ],
)
def test_value_if_missing(row, expected):
    """A missing value takes the fill; a present but unmapped one still comes out null."""
    assert _status(_transformer({**MAPPED, "value_if_missing": "UNKNOWN"}), row) == expected


def test_value_if_missing_covers_missing_values_codes():
    """A code nulled by missing_values is missing too."""
    tr = _transformer({**MAPPED, "missing_values": [8], "value_if_missing": "UNKNOWN"})
    assert _status(tr, {"pid": "P1", "status": 8}) == "UNKNOWN"


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"pid": "P1", "status": 0}, "ABSENT"),
        ({"pid": "P2", "status": 9}, "UNKNOWN"),
        ({"pid": "P3", "status": None}, None),
    ],
)
def test_value_if_unmapped(row, expected):
    """A present value with no mapping takes the fill; a missing one still comes out null."""
    assert _status(_transformer({**MAPPED, "value_if_unmapped": "UNKNOWN"}), row) == expected


def test_fill_resolves_against_the_target_enum():
    """A fill spelled by meaning comes out as the permissible value key, like a mapped value."""
    tr = _transformer({**MAPPED, "value_if_missing": "OMOP:45877986", "value_if_unmapped": "OMOP:45877986"})
    assert _status(tr, {"pid": "P1", "status": None}) == "UNKNOWN"
    assert _status(tr, {"pid": "P2", "status": 9}) == "UNKNOWN"


def test_value_if_missing_skips_offset():
    """The fill is a target value, so an offset isn't added to it."""
    years = {"value_if_missing": 0, "offset": {"offset_value": 365, "offset_field": "status"}}
    tr = _transformer({}, years=years)
    assert tr.map_object({"pid": "P1", "status": 1, "years": None}, source_type="answers")["years"] == 0


def test_without_fills_behaviour_is_unchanged():
    """With neither field set, missing and unmapped values come out null as before."""
    tr = _transformer(MAPPED)
    assert _status(tr, {"pid": "P1", "status": None}) is None
    assert _status(tr, {"pid": "P2", "status": 9}) is None


def test_streamed_empty_cell_takes_the_fill(tmp_path):
    """An empty TSV cell is missing, through the streaming engine."""
    (tmp_path / "answers.tsv").write_text("pid\tstatus\nP1\t1\nP2\t\nP3\t9\n")
    tr = _transformer({**MAPPED, "value_if_missing": "UNKNOWN", "value_if_unmapped": "UNKNOWN"})
    results = list(transform_spec(tr, DataLoader(tmp_path, schemaview=tr.source_schemaview)))
    assert [r["status"] for r in results] == ["PRESENT", "UNKNOWN", "UNKNOWN"]
