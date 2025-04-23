"""
Tests engine for deriving schemas (profiling) from a specification and a source.
"""

import pytest
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


@pytest.fixture
def source_schemaview() -> SchemaView:
    """Instantiate a schemaview with Schema1."""
    return SchemaView(SCHEMA1)


@pytest.fixture
def mapper(source_schemaview: SchemaView) -> SchemaMapper:
    """Instantiate a mapper with Schema1 as the source schema."""
    mapper = SchemaMapper()
    mapper.source_schemaview = source_schemaview
    return mapper


def test_derive_schema(mapper: SchemaMapper, source_schemaview: SchemaView) -> None:
    """Tests deriving a schema from a specification and a source."""
    tr = ObjectTransformer()
    tr.source_schemaview = source_schemaview
    tr.load_transformer_specification(SPECIFICATION)
    target_schema = mapper.derive_schema(tr.specification)
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
        assert cn in target_schema.classes
        c = target_schema.classes[cn]
        atts = c.attributes
        for s in ex_slots:
            assert s in atts
    agent = target_schema.classes["Agent"]
    assert agent.is_a == "Entity"


def test_null_specification(mapper: SchemaMapper) -> None:
    """
    Tests empty spec limit case.

    An empty spec should return an empty schema.
    """
    specification = TransformationSpecification(id="test")
    target_schema = mapper.derive_schema(specification)
    assert list(target_schema.classes.values()) == []


def test_null_specification_and_source() -> None:
    """
    Tests empty spec and source schema limit case.

    An empty spec and source schema should return an empty schema.
    """
    tr = SchemaMapper()
    tr.source_schemaview = SchemaView(SCHEMA1)
    specification = TransformationSpecification(id="test")
    target_schema = tr.derive_schema(specification)
    assert list(target_schema.classes.values()) == []


def test_definition_in_derivation() -> None:
    """
    Test where the derived schema is entirely specified by the spec.
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
    assert {"Agent", "Thing"} == set(target_schema.classes.keys())

    thing = target_schema.classes["Thing"]
    atts = thing.attributes
    assert list(atts.keys()) == ["id"]
    id_att = atts["id"]
    assert id_att.range == "uriorcurie"
    assert id_att.identifier
    agent = target_schema.classes["Agent"]
    assert agent.is_a == "Thing"


def test_derive_partial(mapper: SchemaMapper) -> None:
    """
    Tests partial spec limit case.
    """
    specification = TransformationSpecification(id="test")
    derivations = [
        ClassDerivation(name="Agent", populated_from="Person"),
    ]
    for derivation in derivations:
        specification.class_derivations[derivation.name] = derivation
    target_schema = mapper.derive_schema(specification)
    print(yaml_dumper.dumps(target_schema))
    assert list(target_schema.classes.keys()) == ["Agent"]


def test_rewire() -> None:
    """
    Tests rewire.

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
    assert list(target_schema.classes.values()) == []
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
    assert list(target_schema.classes.keys()) == ["TrEmployee"]
    emp = target_schema.classes["TrEmployee"]
    assert list(emp.attributes.keys()) == ["tr_salary"]
    specification.class_derivations["TrEmployee"].is_a = "Person"
    target_schema = tr.derive_schema(specification)
    assert list(target_schema.classes.keys()) == ["TrEmployee"]
    emp = target_schema.classes["TrEmployee"]
    assert list(emp.attributes.keys()) == ["tr_salary"]


def test_full_copy_specification(mapper: SchemaMapper) -> None:
    """Tests copy isomorphism."""
    copy_all_directive = {"*": CopyDirective(element_name="*", copy_all=True)}
    specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
    source_schema = mapper.source_schemaview.schema

    target_schema = mapper.derive_schema(specification)
    # classes, slots and enums must be exactly the same
    assert yaml_dumper.dumps(source_schema.classes) == yaml_dumper.dumps(target_schema.classes)
    assert yaml_dumper.dumps(source_schema.slots) == yaml_dumper.dumps(target_schema.slots)
    assert yaml_dumper.dumps(source_schema.enums) == yaml_dumper.dumps(target_schema.enums)


def test_partial_copy_specification(mapper: SchemaMapper) -> None:
    """Tests copy isomorphism excluding derivations."""
    copy_all_directive = {"*": CopyDirective(element_name="*", copy_all=True)}
    specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
    source_schema = mapper.source_schemaview.schema

    derivations = [
        ClassDerivation(name="Agent", populated_from="Person"),
    ]
    for derivation in derivations:
        specification.class_derivations[derivation.name] = derivation
    target_schema = mapper.derive_schema(specification)
    # classes must be the same with addition
    for schema_class in source_schema.classes:
        assert schema_class in target_schema.classes, f"Class '{schema_class}' is missing in target"
    assert "Agent" in target_schema.classes, "Derived class 'Agent' is missing in target"
    # slots and enums must be exactly the same
    assert yaml_dumper.dumps(source_schema.slots) == yaml_dumper.dumps(target_schema.slots)
    assert yaml_dumper.dumps(source_schema.enums) == yaml_dumper.dumps(target_schema.enums)


def test_full_copy_class(mapper: SchemaMapper) -> None:
    """Tests copy isomorphism with class derivation."""
    copy_all_directive = {"*": CopyDirective(element_name="*", copy_all=True)}
    specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
    source_schema = mapper.source_schemaview.schema

    derivations = [
        ClassDerivation(name="Agent", populated_from="Person", copy_directives=copy_all_directive),
    ]
    for derivation in derivations:
        specification.class_derivations[derivation.name] = derivation
    target_schema = mapper.derive_schema(specification)
    # classes must be the same with addition
    for schema_class in source_schema.classes:
        assert schema_class in target_schema.classes, f"Class '{schema_class}' is missing in target"
    assert "Agent" in target_schema.classes, "Derived class 'Agent' is missing in target"
    assert yaml_dumper.dumps(source_schema.classes["Person"].slots) == yaml_dumper.dumps(
        target_schema.classes["Agent"].slots
    )
    assert yaml_dumper.dumps(source_schema.classes["Person"].attributes) == yaml_dumper.dumps(
        target_schema.classes["Agent"].attributes
    )
    # slots and enums must be exactly the same
    assert yaml_dumper.dumps(source_schema.slots) == yaml_dumper.dumps(target_schema.slots)
    assert yaml_dumper.dumps(source_schema.enums) == yaml_dumper.dumps(target_schema.enums)


def test_copy_blacklisting(mapper: SchemaMapper) -> None:
    """Tests copy on a blacklist approach."""
    blacklist = ["Person"]
    copy_all_directive = {"*": CopyDirective(element_name="*", copy_all=True, exclude=blacklist)}
    specification = TransformationSpecification(id="test", copy_directives=copy_all_directive)
    source_schema = mapper.source_schemaview.schema

    derivations = [
        ClassDerivation(name="Agent", populated_from="Person"),
    ]
    for derivation in derivations:
        specification.class_derivations[derivation.name] = derivation
    target_schema = mapper.derive_schema(specification)
    # classes must be the same with addition
    for schema_class in source_schema.classes:
        if schema_class in blacklist:
            assert schema_class not in target_schema.classes, (
                f"Class '{schema_class}' is missing in target"
            )
        else:
            assert schema_class in target_schema.classes, (
                f"Class '{schema_class}' is missing in target"
            )
    assert "Agent" in target_schema.classes, "Derived class 'Agent' is missing in target"

    # slots and enums must be exactly the same
    assert yaml_dumper.dumps(source_schema.slots) == yaml_dumper.dumps(target_schema.slots)
    assert yaml_dumper.dumps(source_schema.enums) == yaml_dumper.dumps(target_schema.enums)


def test_copy_whitelisting(mapper: SchemaMapper) -> None:
    """Tests copy on a whitelist approach."""
    whitelist = ["NamedThing"]
    whitelist_directive = {
        "Whitelist": CopyDirective(
            element_name="*", copy_all=True, exclude_all=True, include=whitelist
        )
    }
    specification = TransformationSpecification(id="test", copy_directives=whitelist_directive)
    source_schema = mapper.source_schemaview.schema

    derivations = [
        ClassDerivation(name="Agent", populated_from="Person"),
    ]
    for derivation in derivations:
        specification.class_derivations[derivation.name] = derivation
    target_schema = mapper.derive_schema(specification)
    # classes, slots and enums must have only what explicitly included
    for schema_class in source_schema.classes:
        if schema_class in whitelist:
            assert schema_class in target_schema.classes, (
                f"Class '{schema_class}' is missing in target"
            )
        else:
            assert schema_class not in target_schema.classes, (
                f"Class '{schema_class}' is missing in target"
            )
    assert "Agent" in target_schema.classes, "Derived class 'Agent' is missing in target"
    for schema_slot in source_schema.slots:
        if schema_slot in whitelist:
            assert schema_slot in target_schema.slots, f"Slot '{schema_slot}' is missing in target"
        else:
            assert schema_slot not in target_schema.slots, (
                f"Slot '{schema_slot}' is missing in target"
            )
    for schema_enum in source_schema.enums:
        if schema_enum in whitelist:
            assert schema_enum in target_schema.enums, f"Enum '{schema_enum}' is missing in target"
        else:
            assert schema_enum not in target_schema.enums, (
                f"Enum '{schema_enum}' is missing in target"
            )


def test_overrides_in_class_derivation(mapper: SchemaMapper) -> None:
    """Test that overrides in ClassDerivation are applied."""
    specification = TransformationSpecification(
        id="test",
        class_derivations={
            "Agent": ClassDerivation(
                name="Agent",
                populated_from="Person",
                overrides={
                    "description": "Like Person, but not in a subset",
                    "in_subset": None,
                },
            )
        },
    )
    target_schema = mapper.derive_schema(specification)
    agent = target_schema.classes["Agent"]
    assert agent.description == "Like Person, but not in a subset"
    assert agent.class_uri == "schema:Person"


def test_overrides_in_slot_derivation(mapper: SchemaMapper) -> None:
    """Test that overrides in SlotDerivation are applied."""
    specification = TransformationSpecification(
        id="test",
        class_derivations={
            "Agent": ClassDerivation(
                name="Agent",
                populated_from="Person",
                slot_derivations={
                    "age_in_years": SlotDerivation(
                        name="age_in_years",
                        overrides={
                            "required": True,
                            "maximum_value": 120,
                            "description": "Age in years, but required and more realistic",
                        },
                    )
                },
            )
        },
    )
    target_schema = mapper.derive_schema(specification)
    agent = target_schema.classes["Agent"]
    age = agent.attributes["age_in_years"]
    assert age.required is True
    assert age.minimum_value == 0
    assert age.maximum_value == 120
    assert age.description == "Age in years, but required and more realistic"


def test_overrides_errors_with_unknown_attribute(mapper: SchemaMapper) -> None:
    """Test that an error is raised if overrides contains attributes not part of the metamodel."""
    specification = TransformationSpecification(
        id="test",
        class_derivations={
            "Agent": ClassDerivation(
                name="Agent",
                populated_from="Person",
                overrides={"unknown_attribute": "This should raise an error"},
            )
        },
    )
    with pytest.raises(TypeError, match="got an unexpected keyword argument 'unknown_attribute'"):
        mapper.derive_schema(specification)

    specification = TransformationSpecification(
        id="test",
        class_derivations={
            "Agent": ClassDerivation(
                name="Agent",
                populated_from="Person",
                slot_derivations={
                    "age_in_years": SlotDerivation(
                        name="age_in_years",
                        overrides={"unknown_attribute": "This should raise an error"},
                    )
                },
            )
        },
    )
    with pytest.raises(TypeError, match="got an unexpected keyword argument 'unknown_attribute'"):
        mapper.derive_schema(specification)
