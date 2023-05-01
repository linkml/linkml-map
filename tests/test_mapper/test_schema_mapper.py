import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import yaml_loader

from linkml_transformer.datamodel.transformer_model import *
from linkml_transformer.schema_mapper.schema_mapper import SchemaMapper
from linkml_transformer.transformer.object_transformer import ObjectTransformer
from tests import SCHEMA1, SPECIFICATION


class SchemaMapperTestCase(unittest.TestCase):
    """
    Tests engine for deriving schemas
    """

    def setUp(self) -> None:
        mapper = SchemaMapper()
        tr = ObjectTransformer()
        self.source_schemaview = SchemaView(SCHEMA1)
        mapper.source_schemaview = self.source_schemaview
        tr.source_schemaview = self.source_schemaview
        tr.load_transformer_specification(SPECIFICATION)
        self.transformer = tr
        self.specification = tr.specification
        self.mapper = mapper

    def test_derive_schema(self):
        """tests deriving a schema from a specification and a source"""
        mapper = self.mapper
        target_schema = mapper.derive_schema(self.specification)
        cases = [
            (
                "Agent",
                [
                    "id",
                    "age",
                    "label",
                    "has_familial_relationships",
                    "primary_email",
                    "gender",
                    "current_address",
                ],
            ),
            ("FamilialRelationship", ["related_to", "type"]),
        ]
        for cn, slots in cases:
            self.assertIn(cn, target_schema.classes)
            c = target_schema.classes[cn]
            atts = c.attributes
            for s in slots:
                self.assertIn(s, atts)
            # self.assertCountEqual(slots, list(atts))

    def test_derive_null(self):
        """tests empty spec limit case"""
        tr = self.mapper
        specification = TransformationSpecification(id="test")
        target_schema = tr.derive_schema(specification)
        self.assertEqual([], list(target_schema.classes.values()))

    def test_derive_partial(self):
        """tests empty spec limit case"""
        tr = self.mapper
        specification = TransformationSpecification(id="test")
        derivations = [
            ClassDerivation(name="Agent", populated_from="Person"),
        ]
        for derivation in derivations:
            specification.class_derivations[derivation.name] = derivation
        target_schema = tr.derive_schema(specification)
        print(yaml_dumper.dumps(target_schema))


if __name__ == "__main__":
    unittest.main()
