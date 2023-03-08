import itertools
import unittest

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import ClassDefinition, SlotDefinition, SchemaDefinition
from linkml_runtime.loaders import yaml_loader

import tests.input.examples.flattening.model.denormalized_model as sssom_tgt_dm
import tests.input.examples.flattening.model.normalized_model as sssom_src_dm
import tests.input.examples.personinfo_basic.model.agent_model as tgt_dm
import tests.input.examples.personinfo_basic.model.personinfo_model as src_dm
from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.transformer.object_transformer import ObjectTransformer
from linkml_transformer.utils.dynamic_object import dynamic_object
from tests import (DENORM_SCHEMA, DENORM_SPECIFICATION, FLATTENING_DATA,
                   NORM_SCHEMA, PERSONINFO_DATA, PERSONINFO_SRC_SCHEMA,
                   PERSONINFO_TGT_SCHEMA, PERSONINFO_TR)


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
        print(yaml.dump(target_obj))

    def test_transform_simple_object(self):
        """
        Tests transforming a Person object from s1 to an Agent object in s2
        """
        tr = self.tr
        obj: src_dm.Person
        obj = yaml_loader.load(str(PERSONINFO_DATA), target_class=src_dm.Person)
        self.assertIsInstance(obj, src_dm.Person)
        self.assertEqual(33, obj.age_in_years)
        self.assertEqual(1, len(obj.has_familial_relationships))
        fr = obj.has_familial_relationships[0]
        self.assertIsInstance(fr, src_dm.FamilialRelationship)
        self.assertEqual("P:002", fr.related_to)
        self.assertEqual("SIBLING_OF", str(fr.type))
        self.assertEqual(
            src_dm.FamilialRelationshipType(src_dm.FamilialRelationshipType.SIBLING_OF),
            fr.type,
        )
        target_obj = tr.transform_object(obj, target_class=tgt_dm.Agent)
        print(yaml_dumper.dumps(target_obj))
        self.assertIsInstance(target_obj, tgt_dm.Agent)
        self.assertEqual(obj.name, target_obj.label, "name becomes label")
        self.assertEqual("33 years", target_obj.age, f"Failed to stringify age")
        self.assertIsNone(target_obj.gender, "gender is set to None")
        # self.assertEqual(obj.name, target_obj.label)
        self.assertEqual(
            1, len(target_obj.has_familial_relationships), "relationships are preserved"
        )
        tfr = target_obj.has_familial_relationships[0]
        self.assertIsInstance(tfr, tgt_dm.FamilialRelationship)
        self.assertEqual("P:002", tfr.related_to)
        self.assertEqual("SIBLING_OF", str(tfr.type))

    def test_transform_container_dict(self):
        """tests recursive"""
        tr = self.tr
        person = yaml.safe_load(open(str(PERSONINFO_DATA)))
        container = dict(persons=[person])
        target_obj = tr.transform(container, source_type="Container")
        print(yaml.dump(target_obj))

    def test_transform_container_object(self):
        """tests recursive"""
        tr = self.tr
        person = yaml_loader.load(str(PERSONINFO_DATA), target_class=src_dm.Person)
        obj = src_dm.Container(persons=[person])
        target_obj: tgt_dm.Container = tr.transform_object(
            obj, target_class=tgt_dm.Container
        )
        print(yaml_dumper.dumps(target_obj))
        self.assertIsInstance(target_obj, tgt_dm.Container)
        agents = target_obj.agents
        agent = agents[0]
        self.assertEqual(person.name, agent.label)
        self.assertEqual("33 years", agent.age)
        person_fr1 = person.has_familial_relationships[0]
        agent_fr1 = agent.has_familial_relationships[0]
        self.assertEqual(person_fr1.related_to, agent_fr1.related_to)

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
        self.assertEqual("X:1", mp.subject.id)
        self.assertEqual("x1", mp.subject.name)
        container["mappings"][0]["subject"] = "U:1"
        tr.index(container, "MappingSet")
        dynobj = dynamic_object(container, sv, "MappingSet")
        mset = ix.bless(dynobj)
        print(mset)
        print(mset.mappings)
        print(mset.mappings[0])
        print(mset.mappings[0].object)
        print(mset.mappings[0].object.id)
        print(mset.mappings[0].object.name)
        print(mset.mappings[0].subject)
        # print(mset.mappings[0].subject.id)
        # print(mset.mappings[0].subject.name)

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
        self.assertEqual("X:1", mp.subject.id)
        self.assertEqual("x1", mp.subject.name)
        mset.mappings[0].subject = "U:1"
        tr.index(mset, "MappingSet")
        mset = ix.bless(mset)
        print(mset)
        print(mset.mappings)
        print(mset.mappings[0])
        print(mset.mappings[0].object)
        print(mset.mappings[0].object.id)
        print(mset.mappings[0].object.name)
        print(mset.mappings[0].subject)
        print(mset.mappings[0].subject.id)
        print(mset.mappings[0].subject.name)
        self.assertEqual("U:1", mset.mappings[0].subject.id)
        self.assertIsNone(mset.mappings[0].subject.name)

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
        tr.index(mset, "MappingSet")
        target_obj = tr.transform(mset, source_type="MappingSet")
        print(target_obj)
        print(type(target_obj))

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
                schema = SchemaDefinition(name="test", id="test", classes=[cls], default_range="string")
                return schema
            source_schema = mk(source_multivalued)
            target_schema = mk(target_multivalued, explicit)
            specification = TransformationSpecification("test")
            cd = ClassDerivation(class_name, populated_from=class_name)
            specification.class_derivations[class_name] = cd
            sd = SlotDerivation(att_name, populated_from=att_name)
            if explicit:
                sd.cast_collection_as = CollectionType.MultiValued if target_multivalued else CollectionType.SingleValued
            cd.slot_derivations[att_name] = sd
            source_instance = {att_name: [val] if source_multivalued else val}
            tr = ObjectTransformer(specification=specification,
                                   source_schemaview=SchemaView(source_schema),
                                   target_schemaview=SchemaView(target_schema))
            target_instance = tr.transform(source_instance, class_name)
            self.assertEqual([val] if target_multivalued else val, target_instance[att_name])






if __name__ == "__main__":
    unittest.main()
