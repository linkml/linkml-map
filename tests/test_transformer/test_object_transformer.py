"""Test the object transformer."""

from typing import Any

import pytest
import yaml
from unittest.mock import MagicMock
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import (
    ClassDefinition,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.loaders import yaml_loader
from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview

import tests.input.examples.flattening.model.denormalized_model as sssom_tgt_dm
import tests.input.examples.flattening.model.normalized_model as sssom_src_dm
import tests.input.examples.personinfo_basic.model.agent_model as tgt_dm
import tests.input.examples.personinfo_basic.model.personinfo_model as src_dm
from linkml_map.compiler.tr import TR_TO_MAPPING_TABLES
from linkml_map.datamodel import TR_SCHEMA
from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.utils.dynamic_object import dynamic_object
from tests import (
    DENORM_SCHEMA,
    DENORM_SPECIFICATION,
    FLATTENING_DATA,
    NORM_SCHEMA,
    PERSONINFO_CONTAINER_DATA,
    PERSONINFO_CONTAINER_TGT_DATA,
    PERSONINFO_DATA,
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TGT_DATA,
    PERSONINFO_TGT_SCHEMA,
    PERSONINFO_TR,
)

AGE_STRING = "33 years"
AGE_INT = 33

TARGET_DATA = yaml.safe_load(open(str(PERSONINFO_TGT_DATA)))
TARGET_OBJECT = yaml_loader.load(str(PERSONINFO_TGT_DATA), target_class=tgt_dm.Agent)

CONTAINER_DATA = yaml.safe_load(open(str(PERSONINFO_CONTAINER_TGT_DATA)))
CONTAINER_OBJECT = yaml_loader.load(
    str(PERSONINFO_CONTAINER_TGT_DATA), target_class=tgt_dm.Container
)

def inject_slot(schema_dict: dict, class_name: str, slot_name: str, slot_def: dict):
    schema_dict.setdefault("slots", {})[slot_name] = slot_def
    schema_dict["classes"][class_name].setdefault("slots", []).append(slot_name)

def inject_enum(schema: dict, enum_name: str, values: list[str]) -> None:
    schema["enums"][enum_name] = { "permissible_values": {val: {} for val in values} }

@pytest.fixture
def obj_tr() -> ObjectTransformer:
    """Instantiate an object transformer."""
    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = SchemaView(str(PERSONINFO_SRC_SCHEMA))
    obj_tr.target_schemaview = SchemaView(str(PERSONINFO_TGT_SCHEMA))
    obj_tr.load_transformer_specification(PERSONINFO_TR)
    return obj_tr


def test_transform_dict(obj_tr: ObjectTransformer) -> None:
    """
    Tests transforming a dictionary of Person data into a dictionary of Agent data.
    """
    person_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_DATA)))
    assert person_dict["age_in_years"] == AGE_INT
    target_dict: dict[str, Any] = obj_tr.map_object(person_dict, source_type="Person")
    assert isinstance(target_dict, type(TARGET_DATA))
    assert target_dict["age"] == AGE_STRING
    assert target_dict == TARGET_DATA


def test_transform_dict_in_container(obj_tr: ObjectTransformer) -> None:
    """
    Tests transforming a Person data dict in a Container into an Agent data dict in a Container dict.
    """
    person_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_DATA)))
    container_dict = {"persons": [person_dict]}
    target_dict = obj_tr.map_object(container_dict, source_type="Container")
    assert target_dict == {"agents": [TARGET_DATA]}


def test_transform_multiple_dicts_in_container(obj_tr: ObjectTransformer) -> None:
    """
    Tests transforming several Person data dicts in a Container into Agent data dicts in a Container dicts.
    """
    container_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_CONTAINER_DATA)))
    target_dict: dict[str, Any] = obj_tr.map_object(container_dict, source_type="Container")
    assert target_dict == CONTAINER_DATA


def check_familial_relationships(obj, data_model, expected) -> None:
    """Check FamilialRelationships in a data model."""
    assert len(expected) == len(obj.has_familial_relationships)
    for n in range(len(expected)):
        fr = obj.has_familial_relationships[n]
        assert isinstance(fr, data_model.FamilialRelationship)
        assert expected[n]["related_to"] == fr.related_to
        assert expected[n]["type"] == str(fr.type)


def test_coerce(obj_tr: ObjectTransformer) -> None:
    """Test datatype coercion."""
    x = obj_tr._coerce_datatype("5", "integer")  # noqa: SLF001
    assert x == 5
    x = obj_tr._coerce_datatype(5, "string")  # noqa: SLF001
    assert x == "5"
    x = obj_tr._coerce_datatype(5, "integer")  # noqa: SLF001
    assert x == 5

def test_constant_value_slot_derivation() -> None:
    """
    Tests transforming using a constant value (via `value:` field).
    """
    source_schema: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_SRC_SCHEMA)))
    # No need to inject a source slot since `value:` doesn't need source data

    target_schema: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_TGT_SCHEMA)))
    inject_slot(target_schema, "Agent", "study_name", {"range": "string"})

    transform_spec: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_TR)))
    transform_spec.setdefault("class_derivations", {}).setdefault("Agent", {}) \
                  .setdefault("slot_derivations", {})["study_name"] = {
                      "value": "Framingham",
                      "range": "string",
                  }

    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = SchemaView(yaml.dump(source_schema))
    obj_tr.target_schemaview = SchemaView(yaml.dump(target_schema))
    obj_tr.create_transformer_specification(transform_spec)

    person_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_DATA)))
    target_dict: dict[str, Any] = obj_tr.map_object(person_dict, source_type="Person")

    expected = dict(TARGET_DATA)
    expected["study_name"] = "Framingham"
    assert target_dict == expected

def test_value_mappings() -> None:
    """
    Tests transforming using value mappings.
    """
    source_schema: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_SRC_SCHEMA)))
    work_int_dict = { "range": "integer", "minimum_value": 1, "maximum_value": 2}
    inject_slot(source_schema, "Person", "work_type", work_int_dict)

    target_schema: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_TGT_SCHEMA)))
    inject_enum(target_schema, "WorkEnum", ["Home", "Office", "None"])
    work_enum_dict = {"range": "WorkEnum"}
    inject_slot(target_schema, "Agent", "work_value", work_enum_dict)

    transform_spec: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_TR)))
    transform_spec_dict = {
        "populated_from": "work_type",
        "value_mappings": { "1": "Home", "2": "Office" }
    }
    transform_spec.setdefault("class_derivations", {}).setdefault("Agent", {}) \
              .setdefault("slot_derivations", {})["work_value"] = transform_spec_dict

    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = SchemaView(yaml.dump(source_schema))
    obj_tr.target_schemaview = SchemaView(yaml.dump(target_schema))
    obj_tr.create_transformer_specification(transform_spec)

    person_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_DATA)))
    person_dict["work_type"] = 1
    target_dict: dict[str, Any] = obj_tr.map_object(person_dict, source_type="Person")
    assert target_dict["work_value"] == "Home"
    TARGET_DATA["work_value"] = "Home"
    assert target_dict == TARGET_DATA

def test_object_derivations() -> None:
    """
    Test nested object_derivations inside slot_derivations using YAML transform spec.
    """

    # Build source schema
    sb_source = SchemaBuilder()
    sb_source.add_slot("phv00159563", range="string")
    sb_source.add_slot("phv00159568", range="integer")
    sb_source.add_slot("phv00159569", range="string")
    sb_source.add_slot("phv00159573", range="string")
    sb_source.add_slot("phv00159578", range="integer")
    sb_source.add_slot("phv00159579", range="string")
    sb_source.add_class("Person", slots=["phv00159563", "phv00159568", "phv00159569", "phv00159573", "phv00159578", "phv00159579"])
    sb_source.add_defaults()
    source_schema = sb_source.schema

    # Build target schema
    sb_target = SchemaBuilder()
    sb_target.add_slot("id", range="integer")
    sb_target.add_slot("conditions", range="Condition", multivalued=True, inlined=True)
    sb_target.add_slot("condition_concept", range="string")
    sb_target.add_slot("condition_status", range="string")
    sb_target.add_slot("condition_providence", range="string")
    sb_target.add_class("Participant", slots=["id", "conditions"])
    sb_target.add_class("Condition", slots=["condition_concept", "condition_status", "condition_providence"])
    sb_target.add_defaults()
    target_schema = sb_target.schema

    # Transformation spec in YAML
    transform_spec_yaml = """
    class_derivations:
      Participant:
        populated_from: Person
        slot_derivations:
          id:
            populated_from: phv00159568
          conditions:
            object_derivations:
              - class_derivations:
                  Condition:
                    populated_from: Person
                    slot_derivations:
                      condition_concept:
                        expr: "'HP:0001681'"
                      condition_status:
                        populated_from: phv00159563
                      condition_providence:
                        populated_from: phv00159569
              - class_derivations:
                  Condition:
                    populated_from: Person
                    slot_derivations:
                      condition_concept:
                        expr: "'HP:0001683'"
                      condition_status:
                        populated_from: phv00159573
                      condition_providence:
                        populated_from: phv00159579
    """

    transform_spec = yaml.safe_load(transform_spec_yaml)

    # Source input
    input_data = {
        "phv00159563": "PRESENT",
        "phv00159568": 123947,
        "phv00159569": "1",
        "phv00159573": "ABSENT",
        "phv00159578": 123947,
        "phv00159579": "2",
    }

    # Expected target output
    expected_output = {
        "id": 123947,
        "conditions": [
            {
                "condition_concept": "HP:0001681",
                "condition_status": "PRESENT",
                "condition_providence": "1",
            },
                        {
                "condition_concept": "HP:0001683",
                "condition_status": "ABSENT",
                "condition_providence": "2",
            }
        ]
    }
    
    # Create ObjectTransformer and apply transformation
    transformer = ObjectTransformer(unrestricted_eval=True)
    transformer.source_schemaview = SchemaView(source_schema)
    transformer.target_schemaview = SchemaView(target_schema)
    transformer.create_transformer_specification(transform_spec)

    result = transformer.map_object(input_data, source_type="Person")

    assert result == expected_output


def test_transform_simple_object(obj_tr: ObjectTransformer) -> None:
    """
    Tests transforming a Person object into an Agent object.
    """
    person_obj: src_dm.Person = yaml_loader.load(str(PERSONINFO_DATA), target_class=src_dm.Person)
    assert isinstance(person_obj, src_dm.Person)
    assert person_obj.age_in_years == AGE_INT

    expected = [
        {
            "related_to": "P:002",
            "type": "SIBLING_OF",
            "enum": src_dm.FamilialRelationshipType.SIBLING_OF,
        },
        {
            "related_to": "P:003",
            "type": "CHILD_OF",
            "enum": src_dm.FamilialRelationshipType.CHILD_OF,
        },
    ]
    check_familial_relationships(person_obj, src_dm, expected)
    # TODO: move these tests to `check_familial_relationships` once
    # enum derivations are implemented
    for n in range(len(expected)):
        fr = person_obj.has_familial_relationships[n]
        assert src_dm.FamilialRelationshipType(expected[n]["enum"]) == fr.type

    target_obj = obj_tr.transform_object(person_obj, target_class=tgt_dm.Agent)
    assert isinstance(target_obj, tgt_dm.Agent)
    assert person_obj.name == target_obj.label
    assert target_obj.age == AGE_STRING
    assert target_obj.gender is None

    expected = [
        {
            "related_to": "P:002",
            "type": "SIBLING_OF",
            # TODO: enum derivations
            # "enum": tgt_dm.MyFamilialRelationshipType.SIBLING_OF,
        },
        {
            "related_to": "P:003",
            "type": "CHILD_OF",
            # TODO: enum derivations
            # "enum": tgt_dm.MyFamilialRelationshipType.CHILD_OF,
        },
    ]
    check_familial_relationships(target_obj, tgt_dm, expected)
    assert target_obj == TARGET_OBJECT


def test_transform_container_object(obj_tr: ObjectTransformer) -> None:
    """
    Tests transforming a Container object holding a Person object into Container object holding an Agent object.
    """
    person = yaml_loader.load(str(PERSONINFO_DATA), target_class=src_dm.Person)
    container_obj = src_dm.Container(persons=[person])
    result: tgt_dm.Container = obj_tr.transform_object(container_obj, target_class=tgt_dm.Container)
    assert isinstance(result, tgt_dm.Container)
    agents = result.agents
    agent = agents[0]
    assert agent.label == person.name
    assert agent.age == AGE_STRING
    assert agent == TARGET_OBJECT
    for rel in [0, 1]:
        person_fr1 = person.has_familial_relationships[rel]
        agent_fr1 = agent.has_familial_relationships[rel]
        assert person_fr1.related_to == agent_fr1.related_to


def test_transform_object_container(obj_tr: ObjectTransformer) -> None:
    """
    Tests transforming a Container object holding several Person objects into Container object holding several Agent objects.
    """
    container_obj = yaml_loader.load(str(PERSONINFO_CONTAINER_DATA), target_class=src_dm.Container)
    target_obj = obj_tr.transform_object(container_obj, target_class=tgt_dm.Container)
    assert target_obj.agents[0] == TARGET_OBJECT
    assert target_obj == CONTAINER_OBJECT


def check_subject_object_predicate(
    obj,
    expected,
) -> None:
    assert expected["subject_id"] == obj.subject.id
    assert expected["subject_name"] == obj.subject.name
    assert expected["object_id"] == obj.object.id
    assert expected["object_name"] == obj.object.name
    assert expected["predicate"] == obj.predicate


def test_index_dict() -> None:
    sv = SchemaView(NORM_SCHEMA)
    container = yaml.safe_load(open(str(FLATTENING_DATA)))
    dynobj = dynamic_object(container, sv, "MappingSet")
    m = dynobj.mappings[0]
    tr = ObjectTransformer()
    tr.source_schemaview = sv
    tr.index(container, "MappingSet")
    ix = tr.object_index
    mp = ix.bless(m)
    check_subject_object_predicate(
        mp,
        {
            "subject_id": "X:1",
            "subject_name": "x1",
            "object_id": "Y:1",
            "object_name": "y1",
            "predicate": "P:1",
        },
    )
    container["mappings"][0]["subject"] = "U:1"
    tr.index(container, "MappingSet")
    dynobj = dynamic_object(container, sv, "MappingSet")
    mset = ix.bless(dynobj)
    assert mset.mappings[0].subject == "U:1"
    assert mset.mappings[0].object.id == "Y:1"
    assert mset.mappings[0].object.name == "y1"
    assert mset.mappings[0].predicate == "P:1"


def test_index_obj() -> None:
    sv = SchemaView(NORM_SCHEMA)
    mset: sssom_src_dm.MappingSet = yaml_loader.load(
        str(FLATTENING_DATA), target_class=sssom_src_dm.MappingSet
    )
    m = mset.mappings[0]
    tr = ObjectTransformer()
    tr.source_schemaview = sv
    tr.index(mset, "MappingSet")
    ix = tr.object_index
    mp = ix.bless(m)
    check_subject_object_predicate(
        mp,
        {
            "subject_id": "X:1",
            "subject_name": "x1",
            "object_id": "Y:1",
            "object_name": "y1",
            "predicate": "P:1",
        },
    )

    mset.mappings[0].subject = "U:1"
    tr.index(mset, "MappingSet")
    mset = ix.bless(mset)
    expected = {
        "subject_id": "U:1",
        "subject_name": None,
        "object_id": "Y:1",
        "object_name": "y1",
        "predicate": "P:1",
    }
    check_subject_object_predicate(mset.mappings[0], expected)


def test_denormalized_transform_dict() -> None:
    """
    Tests denormalizing transformation.

    The test input is a normalized Mapping class with subject and object that reference a separate
    entities class, which has id and name fields.

    The denormalized output has fields like subject_id
    """
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(NORM_SCHEMA)
    tr.target_schemaview = SchemaView(DENORM_SCHEMA)
    tr.load_transformer_specification(DENORM_SPECIFICATION)
    mset = yaml.safe_load(open(str(FLATTENING_DATA)))
    assert mset["mappings"] == [{"subject": "X:1", "object": "Y:1", "predicate": "P:1"}]
    assert mset["entities"] == {"X:1": {"name": "x1"}, "Y:1": {"name": "y1"}}
    tr.index(mset, "MappingSet")
    target_obj = tr.map_object(mset, source_type="MappingSet")
    assert isinstance(target_obj, dict)
    assert target_obj["mappings"][0] == {
        "subject_id": "X:1",
        "subject_name": "x1",
        "object_id": "Y:1",
        "object_name": "y1",
        "predicate_id": "P:1",
    }


def test_denormalized_object_transform() -> None:
    """
    Tests denormalizing transformation.

    The test input is a normalized Mapping class with subject and object that reference a separate
    entities class, which has id and name fields.

    The denormalized output has fields like subject_id
    """
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(NORM_SCHEMA)
    tr.target_schemaview = SchemaView(DENORM_SCHEMA)
    tr.target_module = sssom_tgt_dm
    tr.load_transformer_specification(DENORM_SPECIFICATION)
    mset: sssom_src_dm.MappingSet = yaml_loader.load(
        str(FLATTENING_DATA), target_class=sssom_src_dm.MappingSet
    )
    mapping = mset.mappings[0]
    assert mapping.subject == "X:1"
    assert mapping.object == "Y:1"
    assert mset.entities["X:1"].name == "x1"
    assert mset.entities["Y:1"].name == "y1"
    tr.index(mset)
    mset_proxy = tr.object_index.bless(mset)
    assert mset_proxy.mappings[0].subject.id == "X:1"
    assert mset_proxy.mappings[0].subject.name == "x1"
    target_obj: sssom_tgt_dm.MappingSet = tr.transform_object(
        mset, target_class=sssom_tgt_dm.MappingSet
    )
    mapping = target_obj.mappings[0]
    assert mapping.subject_id == "X:1"
    assert mapping.subject_name == "x1"
    assert mapping.object_id == "Y:1"
    assert mapping.object_name == "y1"
    # dangling reference
    mset.mappings[0].subject = "U:1"
    tr.index(mset)
    mset_proxy = tr.object_index.bless(mset)
    assert mset_proxy.mappings[0].subject.id == "U:1"
    assert mset_proxy.mappings[0].subject.name is None
    target_obj = tr.transform_object(mset, target_class=sssom_tgt_dm.MappingSet)
    mapping = target_obj.mappings[0]
    assert mapping.subject_id == "U:1"
    assert mapping.subject_name is None
    assert mapping.object_id == "Y:1"
    assert mapping.object_name == "y1"


@pytest.mark.parametrize("source_multivalued", [True, False])
@pytest.mark.parametrize("target_multivalued", [True, False])
@pytest.mark.parametrize("explicit", [True, False])
def test_cardinalities(source_multivalued: bool, target_multivalued: bool, explicit: bool) -> None:  # noqa: FBT001
    """
    Tests enforcing cardinality.
    """
    class_name = "MyClass"
    att_name = "my_att"
    val = "v1"

    def mk(mv: bool, ex: bool = False) -> SchemaDefinition:
        """
        Generate a schema with a class with an attribute.

        :param mv: whether or not the attribute is multivalued
        :type mv: bool
        :param ex: whether or not the attribute is explicitly defined as multivalued, defaults to False
        :type ex: bool, optional
        :return: _description_
        :rtype: _type_
        """
        cls = ClassDefinition(class_name)
        # TODO: it should not be necessary to set this if present in Transformation
        # att = SlotDefinition(att_name, multivalued=mv and not ex)
        att = SlotDefinition(att_name, multivalued=mv)
        cls.attributes[att.name] = att
        return SchemaDefinition(name="test", id="test", classes=[cls], default_range="string")

    source_schema = mk(source_multivalued)
    target_schema = mk(target_multivalued, explicit)
    specification = TransformationSpecification(id="test")
    cd = ClassDerivation(name=class_name, populated_from=class_name)
    sd = SlotDerivation(name=att_name, populated_from=att_name)
    if explicit:
        sd.cast_collection_as = (
            CollectionType.MultiValued if target_multivalued else CollectionType.SingleValued
        )
    specification.class_derivations[class_name] = cd
    cd.slot_derivations[att_name] = sd
    source_instance = {att_name: [val] if source_multivalued else val}
    tr = ObjectTransformer(
        specification=specification,
        source_schemaview=SchemaView(source_schema),
        target_schemaview=SchemaView(target_schema),
    )
    target_instance = tr.map_object(source_instance, class_name)
    assert [val] if target_multivalued else val == target_instance[att_name]


def test_self_transform() -> None:
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(str(TR_SCHEMA))
    tr.load_transformer_specification(TR_TO_MAPPING_TABLES)
    source_object = yaml.safe_load(open(str(PERSONINFO_TR)))
    normalizer = ReferenceValidator(package_schemaview("linkml_map.datamodel.transformer_model"))
    normalizer.expand_all = True
    source_object = normalizer.normalize(source_object)
    derived = tr.map_object(source_object)
    print(derived)
    print(yaml.dump(derived))

def test_perform_unit_conversion_basic(obj_tr: ObjectTransformer):
    # Prepare a SlotDerivation with a unit_conversion object mock
    uc_mock = MagicMock()
    uc_mock.source_unit = "cm"
    uc_mock.target_unit = "m"
    uc_mock.source_unit_slot = None
    uc_mock.source_magnitude_slot = None
    uc_mock.target_magnitude_slot = None
    uc_mock.target_unit_slot = None

    slot_derivation = MagicMock()
    slot_derivation.unit_conversion = uc_mock
    slot_derivation.populated_from = "length"

    # Prepare source_obj with a numeric value for 'length'
    source_obj = {"length": 120}

    # Mock SchemaView and Slot
    slot_mock = MagicMock()
    slot_mock.unit.ucum_code = "cm"
    slot_mock.unit.iec61360code = None
    slot_mock.unit.symbol = None
    slot_mock.unit.abbreviation = None
    slot_mock.unit.descriptive_name = None
    slot_mock.name = "length"

    # Patch induced_slot to return slot_mock when called
    obj_tr.source_schemaview.induced_slot = MagicMock(return_value=slot_mock)

    # Call the method
    result = obj_tr._perform_unit_conversion(slot_derivation, source_obj, obj_tr.source_schemaview, source_type="SomeType")

    # 120 cm -> 1.2 m expected (assuming convert_units works as expected)
    # If convert_units not mocked, this test depends on it.
    assert abs(result - 1.2) < 1e-6


def test_perform_unit_conversion_structured_value(obj_tr: ObjectTransformer):
    # Prepare unit_conversion with structured input slots
    uc_mock = MagicMock()
    uc_mock.source_unit = "cm"
    uc_mock.target_unit = "m"
    uc_mock.source_unit_slot = "unit"
    uc_mock.source_magnitude_slot = "value"
    uc_mock.target_magnitude_slot = "value_converted"
    uc_mock.target_unit_slot = "unit_converted"

    slot_derivation = MagicMock()
    slot_derivation.unit_conversion = uc_mock
    slot_derivation.populated_from = "measurement"

    # Prepare a structured source_obj with unit and value keys
    source_obj = {"measurement": {"value": 200, "unit": "cm"}}

    # Mock Slot with unit info
    slot_mock = MagicMock()
    slot_mock.unit.ucum_code = "cm"
    slot_mock.unit.iec61360code = None
    slot_mock.unit.symbol = None
    slot_mock.unit.abbreviation = None
    slot_mock.unit.descriptive_name = None
    slot_mock.name = "measurement"

    obj_tr.source_schemaview.induced_slot = MagicMock(return_value=slot_mock)

    result = obj_tr._perform_unit_conversion(slot_derivation, source_obj, obj_tr.source_schemaview, source_type="SomeType")

    # Should return a dict with converted value and unit
    assert isinstance(result, dict)
    assert "value_converted" in result
    assert "unit_converted" in result
    # Check that the converted value is numeric and unit matches target_unit
    assert isinstance(result["value_converted"], (int, float))
    assert result["unit_converted"] == "m"


def test_perform_unit_conversion_missing_value(obj_tr: ObjectTransformer):
    uc_mock = MagicMock()
    uc_mock.source_unit = "cm"
    uc_mock.target_unit = "m"
    uc_mock.source_unit_slot = None
    uc_mock.source_magnitude_slot = None
    uc_mock.target_magnitude_slot = None
    uc_mock.target_unit_slot = None

    slot_derivation = MagicMock()
    slot_derivation.unit_conversion = uc_mock
    slot_derivation.populated_from = "missing_length"

    source_obj = {}  # no 'missing_length' key

    # Should return None if source value missing
    result = obj_tr._perform_unit_conversion(slot_derivation, source_obj, obj_tr.source_schemaview, source_type="SomeType")
    assert result is None


def test_perform_unit_conversion_raise_on_unit_mismatch(obj_tr: ObjectTransformer):
    uc_mock = MagicMock()
    uc_mock.source_unit = "mm"
    uc_mock.target_unit = "m"
    uc_mock.source_unit_slot = None
    uc_mock.source_magnitude_slot = None
    uc_mock.target_magnitude_slot = None
    uc_mock.target_unit_slot = None

    slot_derivation = MagicMock()
    slot_derivation.unit_conversion = uc_mock
    slot_derivation.populated_from = "length"

    source_obj = {"length": 100}

    # Mock Slot with unit 'cm' which conflicts with uc.source_unit 'mm'
    slot_mock = MagicMock()
    slot_mock.unit.ucum_code = "cm"
    slot_mock.unit.iec61360code = None
    slot_mock.unit.symbol = None
    slot_mock.unit.abbreviation = None
    slot_mock.unit.descriptive_name = None
    slot_mock.name = "length"

    obj_tr.source_schemaview.induced_slot = MagicMock(return_value=slot_mock)

    with pytest.raises(ValueError, match="Mismatch in source units"):
        obj_tr._perform_unit_conversion(slot_derivation, source_obj, obj_tr.source_schemaview, source_type="SomeType")
