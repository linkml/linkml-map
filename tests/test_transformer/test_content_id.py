"""Identifiers synthesized from record content when the spec derives none (#342)."""

import copy
import textwrap
from typing import Any

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.validator import validate_spec_semantics

SOURCE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/source
    name: source
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: source
    default_range: string
    imports: [linkml:types]
    classes:
      Row:
        attributes:
          participant: {}
          visit: {}
          observation_type: {}
          method: {}
          value: {}
          unit: {}
          tags: {multivalued: true}
          steps: {multivalued: true}
          note: {}
""")

TARGET_SCHEMA = textwrap.dedent("""\
    id: https://example.org/target
    name: target
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: target
    default_range: string
    imports: [linkml:types]
    classes:
      Measurement:
        attributes:
          id: {identifier: true, required: true}
          associated_participant: {}
          associated_visit: {}
          observation_type: {}
          method_type: {}
          tags: {multivalued: true}
          steps: {multivalued: true, list_elements_ordered: true}
          value_quantity: {range: Quantity, inlined: true}
      Quantity:
        attributes:
          id: {identifier: true, required: true}
          value_decimal: {range: decimal}
          unit: {}
""")

SPEC = {
    "id": "content-id",
    "class_derivations": {
        "Measurement": {
            "populated_from": "Row",
            "slot_derivations": {
                "associated_participant": {"populated_from": "participant"},
                "associated_visit": {"populated_from": "visit"},
                "observation_type": {"populated_from": "observation_type"},
                "method_type": {"populated_from": "method"},
                "tags": {"populated_from": "tags"},
                "steps": {"populated_from": "steps"},
                "_note": {"populated_from": "note", "hide": True},
                "value_quantity": {
                    "class_derivations": {
                        "Quantity": {
                            "populated_from": "Row",
                            "slot_derivations": {
                                "value_decimal": {"populated_from": "value", "range": "float"},
                                "unit": {"populated_from": "unit"},
                            },
                        }
                    }
                },
            },
        }
    },
}

ROW = {
    "participant": "P1",
    "visit": "V1",
    "observation_type": "OBA:VT0000184",
    "method": "lipid assay",
    "value": "52.30",
    "unit": "mg/dL",
    "tags": ["fasting", "exam 1"],
    "steps": ["draw", "spin"],
    "note": "first",
}


def _transform(row: dict[str, Any], spec: dict[str, Any] = SPEC, target: str | None = TARGET_SCHEMA) -> dict:
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    if target is not None:
        tr.target_schemaview = SchemaView(target)
    tr.create_transformer_specification(copy.deepcopy(spec))
    return tr.map_object(row, "Row")


def _with(**changes: Any) -> dict[str, Any]:
    return {**ROW, **changes}


def test_synthesized_id_is_pinned() -> None:
    """The canonical form is a contract: this exact record must always hash to this id.

    If this fails, every content id produced so far has changed.  The expected values
    were computed independently with ``uuid.uuid5`` over the hand-written canonical
    strings ``{"unit":"mg/dL","value_decimal":52.3}`` (Quantity) and the Measurement
    record with ``tags`` sorted, ``steps`` in order, and the nested object's id included.
    """
    out = _transform(ROW)
    assert out["id"] == "e2f19c73-a77b-5b80-90b8-3394ef6f96d3"
    assert out["value_quantity"]["id"] == "199f65b6-2954-565e-912a-b814c2568cd9"
    assert next(iter(out)) == "id"


def test_same_content_same_id_across_transformers() -> None:
    """Ids carry no per-run state, and input key order doesn't matter."""
    reordered = dict(reversed(list(ROW.items())))
    assert _transform(ROW)["id"] == _transform(reordered)["id"]


@pytest.mark.parametrize(
    "changes",
    [
        {"method": "recalibration"},
        {"visit": "V2"},
        {"value": "52.31"},
        {"steps": ["spin", "draw"]},
    ],
)
def test_different_content_different_id(changes: dict[str, Any]) -> None:
    """Records differing in any emitted value, or in the order of an ordered list, get distinct ids.

    The method case is the ARIC HDL one: same participant, visit and observation type.
    """
    assert _transform(ROW)["id"] != _transform(_with(**changes))["id"]


@pytest.mark.parametrize(
    "changes",
    [
        {"tags": ["exam 1", "fasting"]},
        {"value": "52.300"},
        {"note": "a hidden slot is not part of the record"},
    ],
)
def test_equivalent_content_same_id(changes: dict[str, Any]) -> None:
    """Unordered list order, number formatting, and hidden slots don't change the id."""
    assert _transform(ROW)["id"] == _transform(_with(**changes))["id"]


@pytest.mark.parametrize("absent", [{"tags": None}, {"tags": []}])
def test_null_and_empty_count_as_absent(absent: dict[str, Any]) -> None:
    """A missing slot, a null, and an empty list all hash the same."""
    without = {k: v for k, v in ROW.items() if k != "tags"}
    assert _transform(without)["id"] == _transform(_with(**absent))["id"]


def test_explicit_id_derivation_wins() -> None:
    """A spec that derives the identifier keeps its value; nothing is synthesized."""
    spec = copy.deepcopy(SPEC)
    spec["class_derivations"]["Measurement"]["slot_derivations"]["id"] = {"expr": "'M-' + {participant}"}
    assert _transform(ROW, spec)["id"] == "M-P1"


def test_no_target_schema_no_id() -> None:
    """Without a target schema there is no identifier slot to fill."""
    spec = copy.deepcopy(SPEC)
    del spec["class_derivations"]["Measurement"]["slot_derivations"]["value_quantity"]
    assert "id" not in _transform(ROW, spec, target=None)


def test_validator_reports_synthesis_instead_of_missing_derivation() -> None:
    """An underived identifier is reported as synthesized (info), not as a missing required slot."""
    messages = validate_spec_semantics(
        yaml.safe_load(yaml.safe_dump(SPEC)),
        source_schemaview=SchemaView(SOURCE_SCHEMA),
        target_schemaview=SchemaView(TARGET_SCHEMA),
    )
    about_id = [m for m in messages if "'id'" in m.message and m.path.endswith("[Measurement]")]
    assert [(m.severity, m.message) for m in about_id] == [
        ("info", "Identifier slot 'id' has no derivation; it will be synthesized from a hash of the record's content")
    ]
