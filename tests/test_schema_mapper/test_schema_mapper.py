import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils.schema_builder import SchemaBuilder

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.transformer.object_transformer import ObjectTransformer
from tests import SCHEMA1, SPECIFICATION
from tests.input.examples.personinfo_basic.model.personinfo_model import slots


class SchemaMapperTestCase(unittest.TestCase):
    """
    Tests engine for deriving schemas (profiling) from a specification and a source
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
        agent = target_schema.classes["Agent"]
        self.assertEqual(agent.is_a, "Entity")

    def test_null_specification(self):
        """
        tests empty spec limit case.

        An empty spec should return an empty schema.
        """
        tr = self.mapper
        specification = TransformationSpecification(id="test")
        target_schema = tr.derive_schema(specification)
        self.assertEqual([], list(target_schema.classes.values()))

    def test_null_specification_and_source(self):
        """
        tests empty spec and source schema limit case.

        An empty spec and source schema should return an empty schema.
        """
        tr = SchemaMapper()
        tr.source_schemaview = SchemaView(SCHEMA1)
        specification = TransformationSpecification(id="test")
        target_schema = tr.derive_schema(specification)
        self.assertEqual([], list(target_schema.classes.values()))

    def test_definition_in_derivation(self):
        """
        test where the derived schema is entirely specified by the spec.
        """
        tr = SchemaMapper()
        tr.source_schemaview = SchemaView(SCHEMA1)
        specification = TransformationSpecification(
            id="test",
            class_derivations={
                "Thing": ClassDerivation(
                    name="Thing",
                    slot_derivations={
                        "id": SlotDerivation(
                            name="id",
                            target_definition={"identifier": "true", "range": "uriorcurie"},
                        ),
                    },
                ),
                "Agent": ClassDerivation(
                    name="Agent",
                    slot_derivations={
                        "age": SlotDerivation(name="role", target_definition={"range": "integer"}),
                    },
                    target_definition={
                        "description": "A person or organization.",
                        "is_a": "Thing",
                    },
                ),
            },
        )
        target_schema = tr.derive_schema(specification)
        self.assertEqual({"Agent", "Thing"}, set(target_schema.classes.keys()))

        thing = target_schema.classes["Thing"]
        atts = thing.attributes
        self.assertEqual(["id"], list(atts.keys()))
        id_att = atts["id"]
        self.assertEqual("uriorcurie", id_att.range)
        self.assertEqual(True, id_att.identifier)
        agent = target_schema.classes["Agent"]
        assert agent.is_a == "Thing"

    def test_derive_partial(self):
        """
        tests partial spec limit case.
        """
        tr = self.mapper
        specification = TransformationSpecification(id="test")
        derivations = [
            ClassDerivation(name="Agent", populated_from="Person"),
        ]
        for derivation in derivations:
            specification.class_derivations[derivation.name] = derivation
        target_schema = tr.derive_schema(specification)
        print(yaml_dumper.dumps(target_schema))
        self.assertEqual(["Agent"], list(target_schema.classes.keys()))

    def test_rewire(self):
        """
        tests rewire

        An empty spec and source schema should return an empty schema.
        """
        tr = SchemaMapper()
        sb = SchemaBuilder()
        sb.add_slot("id", range="string", identifier=True)
        sb.add_slot("name", range="string")
        sb.add_slot("pets", range="Pet", multivalued=True)
        sb.add_slot("salary", range="integer")
        sb.add_class("Thing", slots=["id", "name"])
        sb.add_class("Person", is_a="Thing", slots=["pets"])
        sb.add_class("Employee", is_a="Person", slots=["salary"])
        sb.add_class("Pet", is_a="Thing", slots=["pets"])
        tr.source_schemaview = SchemaView(sb.schema)
        specification = TransformationSpecification(
            id="test",
        )
        target_schema = tr.derive_schema(specification)
        self.assertEqual([], list(target_schema.classes.values()))
        specification = TransformationSpecification(
            id="test",
            class_derivations={
                "TrEmployee": ClassDerivation(
                    name="TrEmployee",
                    slot_derivations={
                        "tr_salary": SlotDerivation(
                            name="tr_salary",
                            range="decimal",
                        )
                    },
                )
            },
        )
        target_schema = tr.derive_schema(specification)
        self.assertEqual(["TrEmployee"], list(target_schema.classes.keys()))
        emp = target_schema.classes["TrEmployee"]
        self.assertEqual(["tr_salary"], list(emp.attributes.keys()))
        specification.class_derivations["TrEmployee"].is_a = "Person"
        target_schema = tr.derive_schema(specification)
        self.assertEqual(["TrEmployee"], list(target_schema.classes.keys()))
        emp = target_schema.classes["TrEmployee"]
        self.assertEqual(["tr_salary"], list(emp.attributes.keys()))
        # self.assertEqual("Person", emp.is_a)


if __name__ == "__main__":
    unittest.main()
