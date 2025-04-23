"""Tests the data model."""

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
    for clss, spec in trs.class_derivations.items():
        assert class_derivs[clss] == spec.populated_from

    # slot derivations
    agent_slots = trs.class_derivations["Agent"].slot_derivations
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
