import itertools
import unittest

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import (
    ClassDefinition,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.loaders import yaml_loader

import tests.input.examples.flattening.model.denormalized_model as sssom_tgt_dm
import tests.input.examples.flattening.model.normalized_model as sssom_src_dm
import tests.input.examples.personinfo_basic.model.agent_model as tgt_dm
import tests.input.examples.personinfo_basic.model.personinfo_model as src_dm
from linkml_transformer.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_transformer.transformer.object_transformer import ObjectTransformer
from linkml_transformer.utils.dynamic_object import dynamic_object
from tests import (
    DENORM_SCHEMA,
    DENORM_SPECIFICATION,
    FLATTENING_DATA,
    NORM_SCHEMA,
    PERSONINFO_DATA,
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TGT_SCHEMA,
    PERSONINFO_TR,
)

AGE_STRING = "33 years"


class ObjectTransformerTestCase(unittest.TestCase):
    """
    Tests ObjectTransformer
    """

    def setUp(self) -> None:
        tr = ObjectTransformer()
        tr.source_schemaview = SchemaView(str(PERSONINFO_SRC_SCHEMA))
        tr.target_schemaview = SchemaView(str(PERSONINFO_TGT_SCHEMA))
        tr.specification = yaml_loader.load(
            str(PERSONINFO_TR), target_class=TransformationSpecification
        )
        self.tr = tr

    def test_transform_simple_dict(self):
        """
        Tests transforming a Person object from s1 to an Agent object in s2
        """
        tr = self.tr
        obj = yaml.safe_load(open(str(PERSONINFO_DATA)))
        self.assertEqual(33, obj["age_in_years"])
        target_obj = tr.transform(obj, source_type="Person")
        self.assertEqual(AGE_STRING, target_obj["age"])

    def check_familial_relationships(self, obj, data_model, expected):
        self.assertEqual(len(expected), len(obj.has_familial_relationships))
        for n in range(len(expected)):
            fr = obj.has_familial_relationships[n]
            self.assertIsInstance(fr, data_model.FamilialRelationship)
            self.assertEqual(expected[n]["related_to"], fr.related_to)
            self.assertEqual(expected[n]["type"], str(fr.type))

    def test_transform_simple_object(self):
        """
        Tests transforming a Person object from s1 to an Agent object in s2
        """
        tr = self.tr
        obj: src_dm.Person
        obj = yaml_loader.load(str(PERSONINFO_DATA), target_class=src_dm.Person)
        self.assertIsInstance(obj, src_dm.Person)
        self.assertEqual(33, obj.age_in_years)

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
        self.check_familial_relationships(obj, src_dm, expected)
        # TODO: move these tests to `check_familial_relationships` once
        # enum derivations are implemented
        for n in range(len(expected)):
            fr = obj.has_familial_relationships[n]
            self.assertEqual(src_dm.FamilialRelationshipType(expected[n]["enum"]), fr.type)

        target_obj = tr.transform_object(obj, target_class=tgt_dm.Agent)
        self.assertIsInstance(target_obj, tgt_dm.Agent)
        self.assertEqual(obj.name, target_obj.label, "name becomes label")
        self.assertEqual(AGE_STRING, target_obj.age, "age stringified")
        self.assertIsNone(target_obj.gender, "gender is set to None")
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

    def test_transform_container_dict(self):
        """tests recursive"""
        tr = self.tr
        person = yaml.safe_load(open(str(PERSONINFO_DATA)))
        container = {"persons": [person]}
        target_obj = tr.transform(container, source_type="Container")
        self.assertEqual(list(target_obj.keys()), ["agents"])
        self.assertEqual(target_obj["agents"][0]["age"], AGE_STRING)

    def test_transform_container_object(self):
        """tests recursive"""
        tr = self.tr
        person = yaml_loader.load(str(PERSONINFO_DATA), target_class=src_dm.Person)
        obj = src_dm.Container(persons=[person])
        target_obj: tgt_dm.Container = tr.transform_object(obj, target_class=tgt_dm.Container)
        self.assertIsInstance(target_obj, tgt_dm.Container)
        agents = target_obj.agents
        agent = agents[0]
        self.assertEqual(person.name, agent.label)
        self.assertEqual(AGE_STRING, agent.age)
        for rel in [0, 1]:
            person_fr1 = person.has_familial_relationships[rel]
            agent_fr1 = agent.has_familial_relationships[rel]
            self.assertEqual(person_fr1.related_to, agent_fr1.related_to)

    def check_subject_object_predicate(
        self,
        obj,
        expected={
            "subject_id": "X:1",
            "subject_name": "x1",
            "object_id": "Y:1",
            "object_name": "y1",
            "predicate": "P:1",
        },
    ):
        self.assertEqual(expected["subject_id"], obj.subject.id)
        self.assertEqual(expected["subject_name"], obj.subject.name)
        self.assertEqual(expected["object_id"], obj.object.id)
        self.assertEqual(expected["object_name"], obj.object.name)
        self.assertEqual(expected["predicate"], obj.predicate)

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
        self.check_subject_object_predicate(mp)
        container["mappings"][0]["subject"] = "U:1"
        tr.index(container, "MappingSet")
        dynobj = dynamic_object(container, sv, "MappingSet")
        mset = ix.bless(dynobj)
        self.assertEqual("U:1", mset.mappings[0].subject)
        self.assertEqual("Y:1", mset.mappings[0].object.id)
        self.assertEqual("y1", mset.mappings[0].object.name)
        self.assertEqual("P:1", mset.mappings[0].predicate)

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
        self.check_subject_object_predicate(mp)

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
        tr.specification = yaml_loader.load(
            DENORM_SPECIFICATION, target_class=TransformationSpecification
        )
        mset = yaml.safe_load(open(str(FLATTENING_DATA)))
        self.assertEqual(
            mset["mappings"], [{"subject": "X:1", "object": "Y:1", "predicate": "P:1"}]
        )
        self.assertEqual(mset["entities"], {"X:1": {"name": "x1"}, "Y:1": {"name": "y1"}})
        tr.index(mset, "MappingSet")
        target_obj = tr.transform(mset, source_type="MappingSet")
        assert type(target_obj) == dict
        self.assertEqual(
            target_obj["mappings"][0],
            {
                "subject_id": "X:1",
                "subject_name": "x1",
                "object_id": "Y:1",
                "object_name": "y1",
                "predicate_id": "P:1",
            },
        )

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
        tr.specification = yaml_loader.load(
            DENORM_SPECIFICATION, target_class=TransformationSpecification
        )
        mset: sssom_src_dm.MappingSet = yaml_loader.load(
            str(FLATTENING_DATA), target_class=sssom_src_dm.MappingSet
        )
        mapping = mset.mappings[0]
        self.assertEqual(mapping.subject, "X:1")
        self.assertEqual(mapping.object, "Y:1")
        self.assertEqual(mset.entities["X:1"].name, "x1")
        self.assertEqual(mset.entities["Y:1"].name, "y1")
        tr.index(mset)
        mset_proxy = tr.object_index.bless(mset)
        self.assertEqual(mset_proxy.mappings[0].subject.id, "X:1")
        self.assertEqual(mset_proxy.mappings[0].subject.name, "x1")
        target_obj: sssom_tgt_dm.MappingSet = tr.transform_object(
            mset, target_class=sssom_tgt_dm.MappingSet
        )
        mapping = target_obj.mappings[0]
        self.assertEqual(mapping.subject_id, "X:1")
        self.assertEqual(mapping.subject_name, "x1")
        self.assertEqual(mapping.object_id, "Y:1")
        self.assertEqual(mapping.object_name, "y1")
        # dangling reference
        mset.mappings[0].subject = "U:1"
        tr.index(mset)
        mset_proxy = tr.object_index.bless(mset)
        self.assertEqual(mset_proxy.mappings[0].subject.id, "U:1")
        self.assertIsNone(mset_proxy.mappings[0].subject.name)
        target_obj = tr.transform_object(mset, target_class=sssom_tgt_dm.MappingSet)
        mapping = target_obj.mappings[0]
        self.assertEqual(mapping.subject_id, "U:1")
        self.assertIsNone(mapping.subject_name)
        self.assertEqual(mapping.object_id, "Y:1")
        self.assertEqual(mapping.object_name, "y1")

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
            specification = TransformationSpecification("test")
            cd = ClassDerivation(class_name, populated_from=class_name)
            specification.class_derivations[class_name] = cd
            sd = SlotDerivation(att_name, populated_from=att_name)
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
            target_instance = tr.transform(source_instance, class_name)
            self.assertEqual([val] if target_multivalued else val, target_instance[att_name])


if __name__ == "__main__":
    unittest.main()
