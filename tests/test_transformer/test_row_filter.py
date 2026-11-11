"""A class derivation's ``filter_rows`` limits it to the source rows it applies to."""

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map import ObjectTransformer
from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.errors import TransformationError

SOURCE = """\
id: https://example.org/s
name: s
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string
classes:
  exams:
    attributes:
      pid:
        identifier: true
      exam:
        range: integer
      sbp:
        range: integer
  people:
    attributes:
      pid:
        identifier: true
      cohort:
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
  Visit:
    attributes:
      id:
        identifier: true
      label:
      measurements:
        range: Measurement
        multivalued: true
        inlined_as_list: true
  Measurement:
    attributes:
      value:
        range: integer
"""


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "exams.tsv").write_text("pid\texam\tsbp\nP1\t1\t120\nP2\t2\t130\nP3\t1\t\nP4\t\t140\n")
    (tmp_path / "people.tsv").write_text("pid\tcohort\nP1\toffspring\nP2\toriginal\nP3\toffspring\nP4\toriginal\n")
    return tmp_path


def _transformer(class_derivations: dict) -> ObjectTransformer:
    spec = yaml.safe_load(yaml.dump({"class_derivations": class_derivations}, sort_keys=False))
    return ObjectTransformer(
        specification=spec, source_schemaview=SchemaView(SOURCE), target_schemaview=SchemaView(TARGET)
    )


def _stream(class_derivations: dict, data_dir, on_error=None) -> list[dict]:
    tr = _transformer(class_derivations)
    return list(transform_spec(tr, DataLoader(data_dir, schemaview=tr.source_schemaview), on_error=on_error))


def _visit(**extra) -> dict:
    return {
        "populated_from": "exams",
        **extra,
        "slot_derivations": {"id": {"expr": "{pid} + ':exam1'"}, "label": {"value": "EXAM 1"}},
    }


def test_filter_emits_only_matching_rows(data_dir):
    """Rows the filter rejects yield no record, rather than a record missing its id."""
    assert _stream({"Visit": _visit(filter_rows="{exam} == 1")}, data_dir) == [
        {"id": "P1:exam1", "label": "EXAM 1"},
        {"id": "P3:exam1", "label": "EXAM 1"},
    ]


def test_filter_on_missing_value_rejects_row(data_dir):
    """A filter that evaluates to None, as on an empty cell, rejects the row."""
    results = _stream({"Visit": _visit(filter_rows="{exam} >= 1")}, data_dir)
    assert [r["id"] for r in results] == ["P1:exam1", "P2:exam1", "P3:exam1"]


def test_filter_can_read_a_joined_table(data_dir):
    """A cross-table reference in the filter gets its join synthesized like any expression."""
    results = _stream({"Visit": _visit(filter_rows='{people.cohort} == "original"')}, data_dir)
    assert [r["id"] for r in results] == ["P2:exam1", "P4:exam1"]


def test_filter_on_nested_derivation_drops_the_object(data_dir):
    """A nested derivation whose filter rejects the row contributes no object to the slot."""
    nested = [{"Measurement": {"filter_rows": "{sbp} > 125", "slot_derivations": {"value": {"populated_from": "sbp"}}}}]
    visit = {
        "populated_from": "exams",
        "slot_derivations": {"id": {"populated_from": "pid"}, "measurements": {"class_derivations": nested}},
    }
    results = _stream({"Visit": visit}, data_dir)
    assert results == [
        {"id": "P1", "measurements": []},
        {"id": "P2", "measurements": [{"value": 130}]},
        {"id": "P3", "measurements": []},
        {"id": "P4", "measurements": [{"value": 140}]},
    ]


def test_map_object_returns_none_for_rejected_row():
    """Mapping a single object that fails the filter gives None."""
    tr = _transformer({"Visit": _visit(filter_rows="{exam} == 1")})
    assert tr.map_object({"pid": "P2", "exam": 2}, source_type="exams") is None
    assert tr.map_object({"pid": "P1", "exam": 1}, source_type="exams") == {"id": "P1:exam1", "label": "EXAM 1"}


def test_filter_error_reaches_on_error(data_dir):
    """A filter that fails to evaluate is a row error, reported like a slot error."""
    errors = []
    results = _stream({"Visit": _visit(filter_rows="no_such_function({exam})")}, data_dir, on_error=errors.append)
    assert results == []
    assert errors
    assert all(isinstance(e, TransformationError) and e.class_derivation_name == "Visit" for e in errors)
