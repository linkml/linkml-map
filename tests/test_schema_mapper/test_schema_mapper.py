import unittest

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CopyDirective,
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
