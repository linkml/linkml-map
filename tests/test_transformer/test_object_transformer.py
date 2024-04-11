import itertools
import unittest
from typing import Any

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import (
    ClassDefinition,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.loaders import yaml_loader
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


class ObjectTransformerTestCase(unittest.TestCase):
    """
    Tests ObjectTransformer
    """

    def setUp(self) -> None:
        tr = ObjectTransformer(unrestricted_eval=True)
        tr.source_schemaview = SchemaView(str(PERSONINFO_SRC_SCHEMA))
        tr.target_schemaview = SchemaView(str(PERSONINFO_TGT_SCHEMA))
        tr.load_transformer_specification(PERSONINFO_TR)
        self.tr: ObjectTransformer = tr

    def test_transform_dict(self) -> None:
        """
        Tests transforming a dictionary of Person data
        into a dictionary of Agent data
        """
        tr = self.tr
        person_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_DATA)))
        assert person_dict["age_in_years"] == AGE_INT
        target_dict: dict[str, Any] = tr.map_object(person_dict, source_type="Person")
        assert isinstance(target_dict, type(TARGET_DATA))
        assert target_dict["age"] == AGE_STRING
        assert target_dict == TARGET_DATA

    def test_transform_dict_in_container(self):
        """
        Tests transforming a Person data dict in a Container
        into an Agent data dict in a Container dict
        """
        tr = self.tr
        person_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_DATA)))
        container_dict = {"persons": [person_dict]}
        target_dict = tr.map_object(container_dict, source_type="Container")
        assert target_dict == {"agents": [TARGET_DATA]}

    def test_transform_multiple_dicts_in_container(self) -> None:
        """
        Tests transforming several Person data dicts in a Container
        into Agent data dicts in a Container dicts
        """
        tr = self.tr
        container_dict: dict[str, Any] = yaml.safe_load(open(str(PERSONINFO_CONTAINER_DATA)))
        target_dict: dict[str, Any] = tr.map_object(container_dict, source_type="Container")
        assert target_dict == CONTAINER_DATA

    def check_familial_relationships(self, obj, data_model, expected):
        assert len(expected) == len(obj.has_familial_relationships)
        for n in range(len(expected)):
            fr = obj.has_familial_relationships[n]
            assert isinstance(fr, data_model.FamilialRelationship)
            assert expected[n]["related_to"] == fr.related_to
            assert expected[n]["type"] == str(fr.type)

    def test_coerce(self):
        tr: ObjectTransformer = self.tr
        x = tr._coerce_datatype("5", "integer")
        self.assertEqual(5, x)
        x = tr._coerce_datatype(5, "string")
        self.assertEqual("5", x)
        x = tr._coerce_datatype(5, "integer")
        self.assertEqual(5, x)

    def test_transform_simple_object(self):
        """
        Tests transforming a Person object
        into an Agent object
        """
        tr: ObjectTransformer = self.tr
        person_obj: src_dm.Person = yaml_loader.load(
            str(PERSONINFO_DATA), target_class=src_dm.Person
        )
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
        self.check_familial_relationships(person_obj, src_dm, expected)
        # TODO: move these tests to `check_familial_relationships` once
        # enum derivations are implemented
        for n in range(len(expected)):
            fr = person_obj.has_familial_relationships[n]
            assert src_dm.FamilialRelationshipType(expected[n]["enum"]) == fr.type

        target_obj = tr.transform_object(person_obj, target_class=tgt_dm.Agent)
        assert isinstance(target_obj, tgt_dm.Agent)
        assert person_obj.name == target_obj.label
        assert AGE_STRING == target_obj.age
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
        self.check_familial_relationships(target_obj, tgt_dm, expected)
        assert target_obj == TARGET_OBJECT

    def test_transform_container_object(self):
        """
        Tests transforming a Container object holding a Person object
        into Container object holding an Agent object
        """
        tr = self.tr
        person = yaml_loader.load(str(PERSONINFO_DATA), target_class=src_dm.Person)
        container_obj = src_dm.Container(persons=[person])
        result: tgt_dm.Container = tr.transform_object(container_obj, target_class=tgt_dm.Container)
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

    def test_transform_object_container(self):
        """
        Tests transforming a Container object holding several Person objects
        into Container object holding several Agent objects
        """
        tr = self.tr
        container_obj = yaml_loader.load(
            str(PERSONINFO_CONTAINER_DATA), target_class=src_dm.Container
        )
        target_obj = tr.transform_object(container_obj, target_class=tgt_dm.Container)
        assert target_obj.agents[0] == TARGET_OBJECT
        assert target_obj == CONTAINER_OBJECT

    def check_subject_object_predicate(
        self,
        obj,
        expected,
    ):
        assert expected["subject_id"] == obj.subject.id
        assert expected["subject_name"] == obj.subject.name
        assert expected["object_id"] == obj.object.id
        assert expected["object_name"] == obj.object.name
        assert expected["predicate"] == obj.predicate

    def test_index_dict(self):
        sv = SchemaView(NORM_SCHEMA)
        container = yaml.safe_load(open(str(FLATTENING_DATA)))
        dynobj = dynamic_object(container, sv, "MappingSet")
        m = dynobj.mappings[0]
        tr = ObjectTransformer()
        tr.source_schemaview = sv
        tr.index(container, "MappingSet")
        ix = tr.object_index
        mp = ix.bless(m)
        self.check_subject_object_predicate(
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
        assert "U:1" == mset.mappings[0].subject
        assert "Y:1" == mset.mappings[0].object.id
        assert "y1" == mset.mappings[0].object.name
        assert "P:1" == mset.mappings[0].predicate

    def test_index_obj(self):
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
        self.check_subject_object_predicate(
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
        self.check_subject_object_predicate(mset.mappings[0], expected)

    def test_denormalized_transform_dict(self):
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

    def test_denormalized_object_transform(self):
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
        self.assertIsNone(mset_proxy.mappings[0].subject.name)
        target_obj = tr.transform_object(mset, target_class=sssom_tgt_dm.MappingSet)
        mapping = target_obj.mappings[0]
        assert mapping.subject_id == "U:1"
        self.assertIsNone(mapping.subject_name)
        assert mapping.object_id == "Y:1"
        assert mapping.object_name == "y1"

    def test_cardinalities(self):
        """
        Tests enforcing cardinality
        """
        tf = [True, False]
        class_name = "MyClass"
        att_name = "my_att"
        val = "v1"
        for source_multivalued, target_multivalued, explicit in itertools.product(tf, tf, tf):

            def mk(mv: bool, explicit: bool = False):
                cls = ClassDefinition(class_name)
                # TODO: it should not be necessary to set this if present in Transformation
                # att = SlotDefinition(att_name, multivalued=mv and not explicit)
                att = SlotDefinition(att_name, multivalued=mv)
                cls.attributes[att.name] = att
                schema = SchemaDefinition(
                    name="test", id="test", classes=[cls], default_range="string"
                )
                return schema

            source_schema = mk(source_multivalued)
            target_schema = mk(target_multivalued, explicit)
            specification = TransformationSpecification(id="test")
            cd = ClassDerivation(name=class_name, populated_from=class_name)
            specification.class_derivations[class_name] = cd
            sd = SlotDerivation(name=att_name, populated_from=att_name)
            if explicit:
                sd.cast_collection_as = (
                    CollectionType.MultiValued
                    if target_multivalued
                    else CollectionType.SingleValued
                )
            cd.slot_derivations[att_name] = sd
            source_instance = {att_name: [val] if source_multivalued else val}
            tr = ObjectTransformer(
                specification=specification,
                source_schemaview=SchemaView(source_schema),
                target_schemaview=SchemaView(target_schema),
            )
            target_instance = tr.map_object(source_instance, class_name)
            assert [val] if target_multivalued else val == target_instance[att_name]

    def test_self_transform(self):
        tr = ObjectTransformer()
        tr.source_schemaview = SchemaView(str(TR_SCHEMA))
        tr.load_transformer_specification(TR_TO_MAPPING_TABLES)
        source_object = yaml.safe_load(open(str(PERSONINFO_TR)))
        normalizer = ReferenceValidator(
            package_schemaview("linkml_map.datamodel.transformer_model")
        )
        normalizer.expand_all = True
        source_object = normalizer.normalize(source_object)
        derived = tr.map_object(source_object)
        print(derived)
        print(yaml.dump(derived))


if __name__ == "__main__":
    unittest.main()
