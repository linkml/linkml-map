"""Tests the data model."""

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.transformer.object_transformer import ObjectTransformer
from tests import PERSONINFO_TR


def test_datamodel() -> None:
    """Check loading/retrieval."""
    tr = ObjectTransformer()
    tr.load_transformer_specification(PERSONINFO_TR)
    trs = tr.specification
    assert trs.model_dump_json() != ""
    assert trs.source_schema == "s1"
    assert trs.target_schema == "s2"

    # class derivations
    class_derivs = {
        "Container": "Container",
        "Entity": None,
        "Agent": "Person",
        "Job": None,
        "Address": "Address",
        "FamilialRelationship": "FamilialRelationship",
        "SequenceFeature": None,
        "DenormMapping": "Mapping",
    }
    for cd in trs.class_derivations:
        assert class_derivs[cd.name] == cd.populated_from

    # slot derivations
    agent_cd = next(cd for cd in trs.class_derivations if cd.name == "Agent")
    agent_slots = agent_cd.slot_derivations
    # populated from
    assert agent_slots["label"].populated_from == "name"

    # one line expression
    assert agent_slots["age"].expr == "str({age_in_years}) + ' years'"

    # multi-line expr
    assert (
        agent_slots["driving_since"].expr
        == 'd_test = [x.important_event_date for x in src.has_important_life_events if str(x.event_name) == "PASSED_DRIVING_TEST"]\nif len(d_test):\n    target = d_test[0]\n'
    )

    assert agent_slots["primary_email"].expr is None
    assert agent_slots["secondary_email"].expr == "NULL"
    # this should be fixed!
    assert agent_slots["gender"].expr == "None"

    assert agent_slots["id"].populated_from is None
    assert agent_slots["id"].expr is None

    # enum derivations
    assert len(trs.enum_derivations) == 1
    assert (
        trs.enum_derivations["MyFamilialRelationshipType"].populated_from
        == "FamilialRelationshipType"
    )
    assert {"SIBLING_OF", "CHILD_OF"} == set(
        trs.enum_derivations["MyFamilialRelationshipType"].permissible_value_derivations.keys()
    )


def test_duplicate_class_derivation_names() -> None:
    """Test that multiple class derivations can target the same class name."""
    spec = TransformationSpecification(
        id="test-dup",
        class_derivations=[
            ClassDerivation(
                name="Condition",
                populated_from="pht004031",
                slot_derivations={
                    "code": SlotDerivation(name="code", populated_from="code_a"),
                },
            ),
            ClassDerivation(
                name="Condition",
                populated_from="pht004047",
                slot_derivations={
                    "code": SlotDerivation(name="code", populated_from="code_b"),
                },
            ),
        ],
    )
    assert len(spec.class_derivations) == 2
    assert spec.class_derivations[0].name == "Condition"
    assert spec.class_derivations[1].name == "Condition"
    assert spec.class_derivations[0].populated_from == "pht004031"
    assert spec.class_derivations[1].populated_from == "pht004047"
    # Each derivation keeps its own slot_derivations
    assert spec.class_derivations[0].slot_derivations["code"].populated_from == "code_a"
    assert spec.class_derivations[1].slot_derivations["code"].populated_from == "code_b"


def test_dict_backward_compat() -> None:
    """Test that dict-style class_derivations construction still works."""
    spec = TransformationSpecification(
        id="test-compat",
        class_derivations={
            "Agent": ClassDerivation(name="Agent", populated_from="Person"),
            "Address": ClassDerivation(name="Address"),
        },
    )
    assert len(spec.class_derivations) == 2
    names = [cd.name for cd in spec.class_derivations]
    assert "Agent" in names
    assert "Address" in names


def test_dict_backward_compat_infers_name() -> None:
    """Test that dict key is used as name when ClassDerivation is passed as a plain dict."""
    spec = TransformationSpecification(
        id="test-infer",
        class_derivations={
            "Agent": {"populated_from": "Person"},
            "Address": {"populated_from": "Address"},
        },
    )
    assert len(spec.class_derivations) == 2
    names = {cd.name for cd in spec.class_derivations}
    assert names == {"Agent", "Address"}


def test_empty_class_derivations() -> None:
    """Test that empty class_derivations works for all input forms."""
    # Default (no argument)
    spec1 = TransformationSpecification(id="empty1")
    assert spec1.class_derivations == []

    # Explicit empty list
    spec2 = TransformationSpecification(id="empty2", class_derivations=[])
    assert spec2.class_derivations == []

    # Explicit empty dict (backward compat)
    spec3 = TransformationSpecification(id="empty3", class_derivations={})
    assert spec3.class_derivations == []


def test_append_class_derivation() -> None:
    """Test that class_derivations can be appended to after construction."""
    spec = TransformationSpecification(id="append-test")
    assert spec.class_derivations == []
    spec.class_derivations.append(
        ClassDerivation(name="Agent", populated_from="Person")
    )
    assert len(spec.class_derivations) == 1
    assert spec.class_derivations[0].name == "Agent"
    # Append a second with the same name (the core use case)
    spec.class_derivations.append(
        ClassDerivation(name="Agent", populated_from="Employee")
    )
    assert len(spec.class_derivations) == 2


def test_class_derivations_serialization_roundtrip() -> None:
    """Test that duplicate-name class_derivations survive serialization roundtrip."""
    spec = TransformationSpecification(
        id="roundtrip",
        class_derivations=[
            ClassDerivation(name="Condition", populated_from="table1"),
            ClassDerivation(name="Condition", populated_from="table2"),
            ClassDerivation(name="Agent", populated_from="Person"),
        ],
    )
    dumped = spec.model_dump()
    assert len(dumped["class_derivations"]) == 3

    # Reconstruct from dump
    spec2 = TransformationSpecification(**dumped)
    assert len(spec2.class_derivations) == 3
    assert spec2.class_derivations[0].populated_from == "table1"
    assert spec2.class_derivations[1].populated_from == "table2"

    # JSON roundtrip
    json_str = spec.model_dump_json()
    spec3 = TransformationSpecification.model_validate_json(json_str)
    assert len(spec3.class_derivations) == 3


def test_class_derivations_from_yaml_list_format(tmp_path) -> None:
    """Test loading class_derivations in list YAML format via create_transformer_specification."""
    yaml_str = """\
id: yaml-list-test
class_derivations:
  - Condition:
      populated_from: pht004031
      slot_derivations:
        code:
          populated_from: code_a
  - Condition:
      populated_from: pht004047
      slot_derivations:
        code:
          populated_from: code_b
  - Agent:
      populated_from: Person
"""
    # Write and load via file
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml_str)

    tr = ObjectTransformer()
    tr.load_transformer_specification(str(spec_path))
    spec = tr.specification

    assert len(spec.class_derivations) == 3
    conditions = [cd for cd in spec.class_derivations if cd.name == "Condition"]
    assert len(conditions) == 2
    assert {cd.populated_from for cd in conditions} == {"pht004031", "pht004047"}


def test_class_derivations_from_yaml_dict_format(tmp_path) -> None:
    """Test that existing dict-format YAML specs still load correctly."""
    yaml_str = """\
id: yaml-dict-test
class_derivations:
  Agent:
    populated_from: Person
    slot_derivations:
      label:
        populated_from: name
  Address:
    populated_from: Address
"""
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml_str)

    tr = ObjectTransformer()
    tr.load_transformer_specification(str(spec_path))
    spec = tr.specification

    assert len(spec.class_derivations) == 2
    names = {cd.name for cd in spec.class_derivations}
    assert names == {"Agent", "Address"}


def test_class_derivations_yaml_none_values(tmp_path) -> None:
    """Test that YAML entries with no body (None value) load correctly."""
    yaml_str = """\
id: yaml-none-test
class_derivations:
  Entity:
  Agent:
    populated_from: Person
"""
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml_str)

    tr = ObjectTransformer()
    tr.load_transformer_specification(str(spec_path))
    spec = tr.specification

    assert len(spec.class_derivations) == 2
    entity_cd = next(cd for cd in spec.class_derivations if cd.name == "Entity")
    assert entity_cd.populated_from is None


def test_get_class_derivation_raises_for_duplicate_names_without_populated_from() -> None:
    """Two derivations with the same name and no populated_from should raise on lookup."""
    spec = TransformationSpecification(
        id="dup-no-pf",
        class_derivations=[
            ClassDerivation(name="Result"),
            ClassDerivation(name="Result"),
        ],
    )
    tr = ObjectTransformer()
    tr.specification = spec
    tr.source_schemaview = SchemaView(
        """\
id: https://example.org/minimal
name: minimal
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Result:
    attributes:
      id:
        range: string
"""
    )
    with pytest.raises(ValueError, match="results=2"):
        tr._get_class_derivation("Result")


def test_create_transformer_specification_dict_input() -> None:
    """Test create_transformer_specification with dict-format input."""
    obj = {
        "id": "dict-input-test",
        "class_derivations": {
            "Agent": {
                "populated_from": "Person",
                "slot_derivations": {
                    "label": {"populated_from": "name"},
                },
            },
        },
    }
    tr = ObjectTransformer()
    tr.create_transformer_specification(obj)
    spec = tr.specification

    assert len(spec.class_derivations) == 1
    assert spec.class_derivations[0].name == "Agent"
    assert spec.class_derivations[0].populated_from == "Person"
