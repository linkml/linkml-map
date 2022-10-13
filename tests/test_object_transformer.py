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

from tests import INPUT_DIR, SCHEMA1, SCHEMA2, SPECIFICATION, DENORM_SPECIFICATION


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
        """ tr """
        tr = self.tr
        obj: src_dm.Person
        obj = yaml_loader.load(str(INPUT_DIR / 'personinfo-s1-example-data-01.yaml'), target_class=src_dm.Person)
        target_obj = tr.transform(obj, target_class=tgt_dm.Agent)
        print(yaml_dumper.dumps(target_obj))
        self.assertIsInstance(target_obj, tgt_dm.Agent)
        self.assertEqual(obj.name, target_obj.label)
        self.assertEqual("33 years", target_obj.age)
        #self.assertEqual(obj.name, target_obj.label)

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



if __name__ == '__main__':
    unittest.main()
