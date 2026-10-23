"""A class derivation built only from constants emits one object and reads no input (#389)."""

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
  participants:
    attributes:
      pid:
        identifier: true
      name:
  Study:
    attributes:
      name:
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
  ResearchStudy:
    attributes:
      id:
        identifier: true
      name:
      project:
        range: Project
        inlined: true
  Project:
    attributes:
      code:
  Participant:
    attributes:
      pid:
        identifier: true
      tag:
  Study:
    attributes:
      id:
      name:
  Base:
    attributes:
      name:
      tag:
"""

STUDY = {"slot_derivations": {"id": {"value": "phs000810"}, "name": {"value": "HCHS"}}}
PARTICIPANT = {"populated_from": "participants", "slot_derivations": {"pid": None}}


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "participants.tsv").write_text("pid\tname\nP1\tAda\nP2\tBo\nP3\tCy\n")
    return tmp_path


def _stream(class_derivations: dict, data_dir) -> list[dict]:
    spec = yaml.safe_load(yaml.dump({"class_derivations": class_derivations}, sort_keys=False))
    tr = ObjectTransformer(
        specification=spec, source_schemaview=SchemaView(SOURCE), target_schemaview=SchemaView(TARGET)
    )
    return list(transform_spec(tr, DataLoader(data_dir, schemaview=tr.source_schemaview)))


def test_constant_block_emits_once(data_dir):
    """The constant block yields one object while the per-row block yields one per participant."""
    results = _stream({"ResearchStudy": STUDY, "Participant": PARTICIPANT}, data_dir)
    assert results == [{"id": "phs000810", "name": "HCHS"}, {"pid": "P1"}, {"pid": "P2"}, {"pid": "P3"}]


def test_nested_constant_block_emits_once(data_dir):
    """Nested class derivations made only of constants keep the block constant."""
    nested = {"class_derivations": [{"name": "Project", "slot_derivations": {"code": {"value": "STUDY"}}}]}
    study = {"slot_derivations": {"id": {"value": "phs000810"}, "project": nested}}
    results = _stream({"ResearchStudy": study, "Participant": PARTICIPANT}, data_dir)
    assert results[0] == {"id": "phs000810", "project": {"code": "STUDY"}}
    assert len(results) == 4


def test_only_constant_blocks_need_no_data(tmp_path):
    """A spec made only of constant blocks runs against an empty data directory."""
    assert _stream({"ResearchStudy": STUDY}, tmp_path) == [{"id": "phs000810", "name": "HCHS"}]


def test_constant_block_does_not_hide_missing_input(tmp_path):
    """The no-input check still fails when the per-row block's table is missing."""
    with pytest.raises(FileNotFoundError, match=r"expected one of \['participants'\]"):
        _stream({"ResearchStudy": STUDY, "Participant": PARTICIPANT}, tmp_path)


@pytest.mark.parametrize(
    "class_derivations",
    [
        pytest.param({"Study": {"slot_derivations": {"name": None}}}, id="bare-slot"),
        pytest.param({"Study": {"slot_derivations": {"name": {"expr": "name"}}}}, id="expr"),
        pytest.param({"Study": STUDY}, id="named-after-source-class"),
        pytest.param(
            {"Base": {"slot_derivations": {"name": None}}, "Study": {"is_a": "Base", **STUDY}},
            id="inherits-row-slot",
        ),
    ],
)
def test_blocks_that_read_a_row_emit_per_row(class_derivations, data_dir):
    """A block that reads anything from a row, or is named after a source class, maps every row of its table."""
    (data_dir / "Study.tsv").write_text("name\nX\nY\n")
    results = _stream({**class_derivations, "Participant": PARTICIPANT}, data_dir)
    assert len(results) == 2 + 3


def test_constant_parent_is_not_emitted(data_dir):
    """A constant block that another block inherits from is a template, not a record."""
    base = {"slot_derivations": {"tag": {"value": "x"}}}
    participant = {"is_a": "Base", **PARTICIPANT}
    assert _stream({"Base": base, "Participant": participant}, data_dir) == [
        {"pid": "P1", "tag": "x"},
        {"pid": "P2", "tag": "x"},
        {"pid": "P3", "tag": "x"},
    ]
