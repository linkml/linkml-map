import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils.schema_builder import SchemaBuilder

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CopyDirective,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.transformer.object_transformer import ObjectTransformer
from tests import SCHEMA1, SPECIFICATION


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
        for cn, ex_slots in cases:
            self.assertIn(cn, target_schema.classes)
            c = target_schema.classes[cn]
            atts = c.attributes
            for s in ex_slots:
                self.assertIn(s, atts)
            # self.assertCountEqual(ex_slots, list(atts))
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

    def test_full_copy_specification(self):
        """tests copy isomorphism"""
        tr = self.mapper
        copy_all_directive = {"*": CopyDirective(element_name="*", copy_all=True)}
        specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
        source_schema = tr.source_schemaview.schema

        target_schema = tr.derive_schema(specification)
        # classes, slots and enums must be exactly the same
        self.assertEqual(
            yaml_dumper.dumps(source_schema.classes), yaml_dumper.dumps(target_schema.classes)
        )
        self.assertEqual(
            yaml_dumper.dumps(source_schema.slots), yaml_dumper.dumps(target_schema.slots)
        )
        self.assertEqual(
            yaml_dumper.dumps(source_schema.enums), yaml_dumper.dumps(target_schema.enums)
        )

    def test_partial_copy_specification(self):
        """tests copy isomorphism excluding derivations"""
        tr = self.mapper
        copy_all_directive = {"*": CopyDirective(element_name="*", copy_all=True)}
        specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
        source_schema = tr.source_schemaview.schema

        derivations = [
            ClassDerivation(name="Agent", populated_from="Person"),
        ]
        for derivation in derivations:
            specification.class_derivations[derivation.name] = derivation
        target_schema = tr.derive_schema(specification)
        # classes must be the same with addition
        for schema_class in source_schema.classes.keys():
            self.assertIn(
                schema_class,
                target_schema.classes.keys(),
                f"Class '{schema_class}' is missing in target",
            )
        self.assertIn(
            "Agent", target_schema.classes.keys(), "Derived class 'Agent' is missing in target"
        )
        # slots and enums must be exactly the same
        self.assertEqual(
            yaml_dumper.dumps(source_schema.slots), yaml_dumper.dumps(target_schema.slots)
        )
        self.assertEqual(
            yaml_dumper.dumps(source_schema.enums), yaml_dumper.dumps(target_schema.enums)
        )

    def test_full_copy_class(self):
        """tests copy isomorphism with class derivation"""
        tr = self.mapper
        copy_all_directive = {"*": CopyDirective(element_name="*", copy_all=True)}
        specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
        source_schema = tr.source_schemaview.schema

        derivations = [
            ClassDerivation(
                name="Agent", populated_from="Person", copy_directives=copy_all_directive
            ),
        ]
        for derivation in derivations:
            specification.class_derivations[derivation.name] = derivation
        target_schema = tr.derive_schema(specification)
        # classes must be the same with addition
        for schema_class in source_schema.classes.keys():
            self.assertIn(
                schema_class,
                target_schema.classes.keys(),
                f"Class '{schema_class}' is missing in target",
            )
        self.assertIn(
            "Agent", target_schema.classes.keys(), "Derived class 'Agent' is missing in target"
        )
        self.assertEqual(
            yaml_dumper.dumps(source_schema.classes["Person"].slots),
            yaml_dumper.dumps(target_schema.classes["Agent"].slots),
        )
        self.assertEqual(
            yaml_dumper.dumps(source_schema.classes["Person"].attributes),
            yaml_dumper.dumps(target_schema.classes["Agent"].attributes),
        )
        # slots and enums must be exactly the same
        self.assertEqual(
            yaml_dumper.dumps(source_schema.slots), yaml_dumper.dumps(target_schema.slots)
        )
        self.assertEqual(
            yaml_dumper.dumps(source_schema.enums), yaml_dumper.dumps(target_schema.enums)
        )

    def test_copy_blacklisting(self):
        """tests copy on a blacklist approach"""
        tr = self.mapper
        blacklist = ["Person"]
        copy_all_directive = {
            "*": CopyDirective(element_name="*", copy_all=True, exclude=blacklist)
        }
        specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
        source_schema = tr.source_schemaview.schema

        derivations = [
            ClassDerivation(name="Agent", populated_from="Person"),
        ]
        for derivation in derivations:
            specification.class_derivations[derivation.name] = derivation
        target_schema = tr.derive_schema(specification)
        # classes must be the same with addition
        for schema_class in source_schema.classes.keys():
            if schema_class in blacklist:
                self.assertNotIn(
                    schema_class,
                    target_schema.classes.keys(),
                    f"Class '{schema_class}' is missing in target",
                )
            else:
                self.assertIn(
                    schema_class,
                    target_schema.classes.keys(),
                    f"Class '{schema_class}' is missing in target",
                )
        self.assertIn(
            "Agent", target_schema.classes.keys(), "Derived class 'Agent' is missing in target"
        )
        # slots and enums must be exactly the same
        self.assertEqual(
            yaml_dumper.dumps(source_schema.slots), yaml_dumper.dumps(target_schema.slots)
        )
        self.assertEqual(
            yaml_dumper.dumps(source_schema.enums), yaml_dumper.dumps(target_schema.enums)
        )

    def test_copy_whitelisting(self):
        """tests copy on a whitelist approach"""
        tr = self.mapper
        whitelist = ["NamedThing"]
        whitelist_directive = {
            "Whitelist": CopyDirective(
                element_name="*", copy_all=True, exclude_all=True, include=whitelist
            )
        }
        specification = TransformationSpecification(id="test", copy_directives=whitelist_directive)
        source_schema = tr.source_schemaview.schema

        derivations = [
            ClassDerivation(name="Agent", populated_from="Person"),
        ]
        for derivation in derivations:
            specification.class_derivations[derivation.name] = derivation
        target_schema = tr.derive_schema(specification)
        # classes, slots and enums must have only what explicitly included
        for schema_class in source_schema.classes.keys():
            if schema_class in whitelist:
                self.assertIn(
                    schema_class,
                    target_schema.classes.keys(),
                    f"Class '{schema_class}' is missing in target",
                )
            else:
                self.assertNotIn(
                    schema_class,
                    target_schema.classes.keys(),
                    f"Class '{schema_class}' is missing in target",
                )
        self.assertIn(
            "Agent", target_schema.classes.keys(), "Derived class 'Agent' is missing in target"
        )
        for schema_slot in source_schema.slots.keys():
            if schema_slot in whitelist:
                self.assertIn(
                    schema_slot,
                    target_schema.slots.keys(),
                    f"Slot '{schema_slot}' is missing in target",
                )
            else:
                self.assertNotIn(
                    schema_slot,
                    target_schema.slots.keys(),
                    f"Slot '{schema_slot}' is missing in target",
                )
        for schema_enum in source_schema.enums.keys():
            if schema_enum in whitelist:
                self.assertIn(
                    schema_enum,
                    target_schema.enums.keys(),
                    f"Enum '{schema_enum}' is missing in target",
                )
            else:
                self.assertNotIn(
                    schema_enum,
                    target_schema.enums.keys(),
                    f"Enum '{schema_enum}' is missing in target",
                )


if __name__ == "__main__":
    unittest.main()
