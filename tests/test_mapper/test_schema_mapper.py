import logging
import os
import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader
from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.mapper.schema_mapper import SchemaMapper
from linkml_transformer.transformer.object_transformer import ObjectTransformer

import tests.model.personinfo_s1 as src_dm
import tests.model.personinfo_s2 as tgt_dm

import tests.model.mapping_norm as sssom_src_dm
import tests.model.mapping_denorm as sssom_tgt_dm

from tests import INPUT_DIR, SCHEMA1, SCHEMA2, SPECIFICATION, DENORM_SPECIFICATION, NORM_SCHEMA, DENORM_SCHEMA


class SchemaMapperTestCase(unittest.TestCase):
    """
    Tests engine for deriving schemas
    """

    def setUp(self) -> None:
        tr = SchemaMapper()
        tr.source_schemaview = SchemaView(SCHEMA1)
        self.specification = yaml_loader.load(SPECIFICATION, target_class=TransformationSpecification)
        self.tr = tr

    def test_derive_schema(self):
        """ tests deriving a schema from a specification and a source """
        tr = self.tr
        target_schema = tr.derive_schema(self.specification)
        cases = [
            ("Agent", ["id", "age", "label", "has_familial_relationships", "primary_email", "gender", "current_address"]),
            ("FamilialRelationship", ["related_to", "type"])
            ]
        for cn, slots in cases:
            self.assertIn(cn, target_schema.classes)
            c = target_schema.classes[cn]
            atts = c.attributes
            for s in slots:
                self.assertIn(s, atts)
            #self.assertCountEqual(slots, list(atts))


    def test_derive_null(self):
        """ tests empty spec limit case """
        tr = self.tr
        specification = TransformationSpecification("test")
        target_schema = tr.derive_schema(specification)
        self.assertEqual([], list(target_schema.classes.values()))

    def test_derive_partial(self):
        """ tests empty spec limit case """
        tr = self.tr
        specification = TransformationSpecification("test")
        derivations = [
            ClassDerivation(name="Agent", populated_from="Person"),
        ]
        for derivation in derivations:
            specification.class_derivations[derivation.name] = derivation
        target_schema = tr.derive_schema(specification)
        print(yaml_dumper.dumps(target_schema))



if __name__ == '__main__':
    unittest.main()
