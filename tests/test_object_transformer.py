import logging
import os
import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader
from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.transformer.object_transformer import ObjectTransformer

import tests.model.personinfo_s1 as src_dm
import tests.model.personinfo_s2 as tgt_dm

import tests.model.mapping_norm as sssom_src_dm
import tests.model.mapping_denorm as sssom_tgt_dm

from tests import INPUT_DIR, SCHEMA1, SCHEMA2, SPECIFICATION, DENORM_SPECIFICATION, NORM_SCHEMA, DENORM_SCHEMA


class ObjectTransformerTestCase(unittest.TestCase):
    """
    Tests ObjectTransformer
    """

    def setUp(self) -> None:
        tr = ObjectTransformer()
        tr.source_schemaview = SchemaView(SCHEMA1)
        tr.target_schemaview = SchemaView(SCHEMA2)
        tr.target_module = tgt_dm
        tr.specification = yaml_loader.load(SPECIFICATION, target_class=TransformationSpecification)
        self.tr = tr

    def test_transform_single_object(self):
        """
        Tests transforming a Person object from s1 to an Agent object in s2
        """
        tr = self.tr
        obj: src_dm.Person
        obj = yaml_loader.load(str(INPUT_DIR / 'personinfo-s1-example-data-01.yaml'), target_class=src_dm.Person)
        self.assertIsInstance(obj, src_dm.Person)
        self.assertEqual(33, obj.age_in_years)
        self.assertEqual(1, len(obj.has_familial_relationships))
        fr = obj.has_familial_relationships[0]
        self.assertIsInstance(fr, src_dm.FamilialRelationship)
        self.assertEqual("P:002", fr.related_to)
        self.assertEqual("SIBLING_OF", str(fr.type))
        self.assertEqual(src_dm.FamilialRelationshipType(src_dm.FamilialRelationshipType.SIBLING_OF), fr.type)
        target_obj = tr.transform(obj, target_class=tgt_dm.Agent)
        print(yaml_dumper.dumps(target_obj))
        self.assertIsInstance(target_obj, tgt_dm.Agent)
        self.assertEqual(obj.name, target_obj.label, "name becomes label")
        self.assertEqual("33 years", target_obj.age, f"Failed to stringify age")
        self.assertIsNone(target_obj.gender, "gender is set to None")
        #self.assertEqual(obj.name, target_obj.label)
        self.assertEqual(1, len(target_obj.has_familial_relationships), "relationships are preserved")
        tfr = target_obj.has_familial_relationships[0]
        self.assertIsInstance(tfr, tgt_dm.FamilialRelationship)
        self.assertEqual("P:002", tfr.related_to)
        self.assertEqual("SIBLING_OF", str(tfr.type))

    def test_transform_container(self):
        """ tests recursive """
        tr = self.tr
        person = yaml_loader.load(str(INPUT_DIR / 'personinfo-s1-example-data-01.yaml'), target_class=src_dm.Person)
        obj = src_dm.Container(persons=[person])
        target_obj: tgt_dm.Container = tr.transform(obj, target_class=tgt_dm.Container)
        print(yaml_dumper.dumps(target_obj))
        self.assertIsInstance(target_obj, tgt_dm.Container)
        agents = target_obj.agents
        agent = agents[0]
        self.assertEqual(person.name, agent.label)
        self.assertEqual("33 years", agent.age)
        person_fr1 = person.has_familial_relationships[0]
        agent_fr1 = agent.has_familial_relationships[0]
        self.assertEqual(person_fr1.related_to, agent_fr1.related_to)


    def test_denormalized_transform(self):
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
        tr.specification = yaml_loader.load(DENORM_SPECIFICATION, target_class=TransformationSpecification)
        mset: sssom_src_dm.MappingSet = yaml_loader.load(str(INPUT_DIR / 'mappingset-norm-example-01.yaml'), target_class=sssom_src_dm.MappingSet)
        mapping = mset.mappings[0]
        self.assertEqual(mapping.subject, "X:1")
        self.assertEqual(mapping.object, "Y:1")
        self.assertEqual(mset.entities["X:1"].name, "x1")
        self.assertEqual(mset.entities["Y:1"].name, "y1")
        tr.index(mset)
        mset_proxy = tr.object_index.bless(mset)
        self.assertEqual(mset_proxy.mappings[0].subject.id, "X:1")
        self.assertEqual(mset_proxy.mappings[0].subject.name, "x1")
        target_obj: sssom_tgt_dm.MappingSet = tr.transform(mset, target_class=sssom_src_dm.MappingSet)
        mapping = target_obj.mappings[0]
        self.assertEqual(mapping.subject_id, "X:1")
        self.assertEqual(mapping.subject_name, "x1")
        self.assertEqual(mapping.object_id, "Y:1")
        self.assertEqual(mapping.object_name, "y1")
        # danging reference
        mset.mappings[0].subject = "U:1"
        tr.index(mset)
        self.assertEqual(mset_proxy.mappings[0].subject.id, "U:1")
        self.assertIsNone(mset_proxy.mappings[0].subject.name)
        mset_proxy = tr.object_index.bless(mset)
        target_obj = tr.transform(mset)
        mapping = target_obj.mappings[0]
        self.assertEqual(mapping.subject_id, "U:1")
        self.assertIsNone(mapping.subject_name)
        self.assertEqual(mapping.object_id, "Y:1")
        self.assertEqual(mapping.object_name, "y1")


if __name__ == '__main__':
    unittest.main()
