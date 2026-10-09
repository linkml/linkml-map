"""Identifiers synthesized from record content when the spec derives none (#342)."""

import copy
import json
import textwrap
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner
from linkml_runtime import SchemaView

from linkml_map.cli.cli import main
from linkml_map.transformer.errors import TransformationError
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
    "mint_ids": True,
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


def _about_id(messages: list) -> list[tuple[str, str]]:
    return [(m.severity, m.message) for m in messages if "'id'" in m.message and m.path.endswith("[Measurement]")]


def _validate(spec: dict[str, Any]) -> list:
    return validate_spec_semantics(
        yaml.safe_load(yaml.safe_dump(spec)),
        source_schemaview=SchemaView(SOURCE_SCHEMA),
        target_schemaview=SchemaView(TARGET_SCHEMA),
    )


def test_validator_reports_minting() -> None:
    """With minting on, an underived identifier is reported as synthesized (info)."""
    assert _about_id(_validate(SPEC)) == [
        ("info", "Identifier slot 'id' has no derivation; it will be synthesized from a hash of the record's content")
    ]


def _spec_with(spec_mint_ids: bool | None, class_mint_ids: bool | None, nested: bool = False) -> dict[str, Any]:
    spec = copy.deepcopy(SPEC)
    del spec["mint_ids"]
    if not nested:
        del spec["class_derivations"]["Measurement"]["slot_derivations"]["value_quantity"]
    if spec_mint_ids is not None:
        spec["mint_ids"] = spec_mint_ids
    if class_mint_ids is not None:
        spec["class_derivations"]["Measurement"]["mint_ids"] = class_mint_ids
    return spec


@pytest.mark.parametrize(
    ("spec_mint_ids", "class_mint_ids", "minted"),
    [
        (None, None, False),
        (False, None, False),
        (True, None, True),
        (None, True, True),
        (False, True, True),
        (True, False, False),
    ],
)
def test_mint_ids_setting(spec_mint_ids: bool | None, class_mint_ids: bool | None, minted: bool) -> None:
    """Minting is opt-in; a class derivation's setting overrides the spec's; otherwise the id is an error."""
    spec = _spec_with(spec_mint_ids, class_mint_ids)
    if minted:
        assert "id" in _transform(ROW, spec)
    else:
        with pytest.raises(TransformationError, match="does not derive identifier slot 'id' and mint_ids is not true"):
            _transform(ROW, spec)


def test_nested_derivation_follows_the_spec_not_its_parent() -> None:
    """A nested class derivation without its own setting follows the spec, not its parent class."""
    spec = _spec_with(None, True, nested=True)
    with pytest.raises(TransformationError, match="'Quantity' does not derive identifier slot 'id'"):
        _transform(ROW, spec)
    spec["class_derivations"]["Measurement"]["slot_derivations"]["value_quantity"]["class_derivations"]["Quantity"][
        "mint_ids"
    ] = True
    out = _transform(ROW, spec)
    assert "id" in out
    assert "id" in out["value_quantity"]


def test_missing_identifiers_covers_nested_derivations() -> None:
    """The whole-spec check reports every derivation without an identifier, nested ones included."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(_spec_with(None, None, nested=True))
    assert tr.missing_identifiers() == [
        "Class derivation 'Measurement' does not derive identifier slot 'id' and mint_ids is not true; "
        "derive it explicitly or set mint_ids: true",
        "Class derivation 'Quantity' does not derive identifier slot 'id' and mint_ids is not true; "
        "derive it explicitly or set mint_ids: true",
    ]
    with pytest.raises(ValueError, match="'Measurement' does not derive"):
        tr.check_identifiers()


def test_validator_errors_when_not_minting() -> None:
    """An identifier that is neither derived nor minted is a validation error."""
    assert _about_id(_validate(_spec_with(None, None))) == [
        (
            "error",
            "Class derivation 'Measurement' does not derive identifier slot 'id' and mint_ids is not true; "
            "derive it explicitly or set mint_ids: true",
        )
    ]


INHERITING_TARGET = textwrap.dedent("""\
    id: https://example.org/inheriting
    name: inheriting
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: inheriting
    default_range: string
    imports: [linkml:types]
    classes:
      Record:
        abstract: true
        attributes:
          id: {identifier: true, required: true}
      Measurement:
        is_a: Record
        attributes:
          observation_type: {}
""")

INHERITING_SPEC = {
    "id": "inheriting",
    "class_derivations": {
        "Record": {"slot_derivations": {"id": {"expr": "'R-' + {participant}"}}},
        "Measurement": {
            "is_a": "Record",
            "populated_from": "Row",
            "slot_derivations": {"observation_type": {"populated_from": "observation_type"}},
        },
    },
}


def test_inherited_id_derivation_and_abstract_classes_need_no_minting() -> None:
    """An id derived by an ancestor derivation counts, and abstract target classes need none."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(INHERITING_TARGET)
    tr.create_transformer_specification(copy.deepcopy(INHERITING_SPEC))
    assert tr.missing_identifiers() == []
    assert tr.map_object(ROW, "Row") == {"id": "R-P1", "observation_type": "OBA:VT0000184"}

    messages = validate_spec_semantics(
        copy.deepcopy(INHERITING_SPEC),
        source_schemaview=SchemaView(SOURCE_SCHEMA),
        target_schemaview=SchemaView(INHERITING_TARGET),
    )
    assert [m for m in messages if "identifier" in m.message] == []


CLI_SPEC = textwrap.dedent("""\
    id: content-id-cli
    class_derivations:
      Measurement:
        populated_from: Row
        slot_derivations:
          associated_participant:
            populated_from: participant
          observation_type:
            populated_from: observation_type
""")


def _map_data(tmp_path: Path, *extra: str) -> tuple[Any, Path]:
    (tmp_path / "source.yaml").write_text(SOURCE_SCHEMA)
    (tmp_path / "target.yaml").write_text(TARGET_SCHEMA)
    (tmp_path / "spec.yaml").write_text(CLI_SPEC)
    (tmp_path / "Row.tsv").write_text("participant\tobservation_type\nP1\tOBA:1\nP2\tOBA:2\n")
    output = tmp_path / "out.jsonl"
    args = [
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
        "jsonl",
        "-o",
        str(output),
        *extra,
        str(tmp_path / "Row.tsv"),
    ]
    return CliRunner().invoke(main, args), output


def test_map_data_refuses_records_without_identifiers(tmp_path: Path) -> None:
    """Without --continue-on-error, a missing identifier stops the run before any output."""
    result, output = _map_data(tmp_path)
    assert result.exit_code != 0
    assert "'Measurement' does not derive identifier slot 'id'" in result.output
    assert not output.exists()


def test_continue_on_error_reports_once_and_still_writes(tmp_path: Path) -> None:
    """--continue-on-error reports the missing identifier once (not per row), writes the records, and exits 1.

    Pre-flight validation also prints the same problem as a static finding; the counted
    error is the ``  - `` line.
    """
    result, output = _map_data(tmp_path, "--continue-on-error")
    assert result.exit_code == 1
    assert result.stderr.count("  - Class derivation 'Measurement' does not derive identifier slot 'id'") == 1
    assert "1 transformation error(s)" in result.stderr
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert rows == [
        {"associated_participant": "P1", "observation_type": "OBA:1"},
        {"associated_participant": "P2", "observation_type": "OBA:2"},
    ]


@pytest.mark.parametrize(
    ("spec_mint_ids", "class_default", "class_mint_ids", "minted"),
    [
        (None, {"mint_ids": True}, None, True),
        (False, {"mint_ids": True}, None, True),
        (True, {"mint_ids": False}, None, False),
        (None, {"mint_ids": True}, False, False),
        (None, {"mint_ids": False}, True, True),
        (None, True, None, True),
    ],
)
def test_class_defaults_precedence(
    spec_mint_ids: bool | None, class_default: Any, class_mint_ids: bool | None, minted: bool
) -> None:
    """A target class's default beats the spec's setting; a derivation's own beats both.

    The last case is the compact ``Class: true`` form.
    """
    spec = _spec_with(spec_mint_ids, class_mint_ids)
    spec["class_defaults"] = {"Measurement": class_default}
    if minted:
        assert "id" in _transform(ROW, spec)
    else:
        with pytest.raises(TransformationError, match="mint_ids is not true"):
            _transform(ROW, spec)


def test_validator_honors_class_defaults_and_rejects_unknown_classes() -> None:
    """class_defaults counts toward minting, and naming a class the target lacks is an error."""
    spec = _spec_with(None, None)
    spec["class_defaults"] = {"Measurement": {"mint_ids": True}, "Measurment": {"mint_ids": True}}
    messages = _validate(spec)
    assert _about_id(messages) == [
        ("info", "Identifier slot 'id' has no derivation; it will be synthesized from a hash of the record's content")
    ]
    assert [(m.severity, m.path, m.message) for m in messages if m.path.startswith("class_defaults")] == [
        (
            "error",
            "class_defaults[Measurment]",
            "class_defaults names 'Measurment', which is not a class in the target schema",
        )
    ]
