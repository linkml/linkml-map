"""Tests of biolink subsetting."""

from pathlib import Path

import pytest
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils.formatutils import camelcase, underscore
from linkml_runtime.utils.schemaview import SchemaView

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CopyDirective,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.session import Session
from linkml_map.utils.loaders import load_specification
from tests import BIOLINK_SRC_SCHEMA, BIOLINK_TR


def get_biolink_class_derivations(sv: SchemaView, subset_classes: list) -> list:
    """
    Get Biolink class derivations.

    :param sv: SchemaView object
    :param subset_classes: List of classes to subset
    :return: List of class derivations incl slot derivations
    """
    # Example implementation to fetch class definitions
    # This should be replaced with the actual implementation
    class_derivations = []
    for class_name in subset_classes:
        class_derivation = ClassDerivation(populated_from=class_name, name=camelcase(class_name))
        induced_slots = sv.class_induced_slots(class_name)
        for slot in induced_slots:
            slot_derivation = SlotDerivation(populated_from=slot.name, name=underscore(slot.name))
            class_derivation.slot_derivations[underscore(slot.name)] = slot_derivation
        class_derivations.append(class_derivation)
    return class_derivations


@pytest.fixture
def biolink_schema() -> SchemaView:
    """
    Fixture to load Biolink schema from vendored local copy.

    :return: SchemaView object for biolink-model
    """
    return SchemaView(str(BIOLINK_SRC_SCHEMA))


def test_biolink_subsetting_manual(
    biolink_schema: SchemaView, tmp_path: Path
) -> None:
    """
    Test to subset the Biolink schema manually.

    :param biolink_schema: Fixture to load Biolink schema
    """
    transform_file = BIOLINK_TR
    # Initialize Session and SchemaBuilder
    session = Session()

    # Set the source schema in the session
    session.set_source_schema(biolink_schema)

    tr_spec = load_specification(transform_file)
    mapper = SchemaMapper()
    mapper.source_schemaview = biolink_schema

    target_schema_obj = mapper.derive_schema(
        specification=tr_spec,
        target_schema_id="biolink-profile",
        target_schema_name="BiolinkProfile",
    )

    # Remove non-linkml imports so derived schema is standalone
    # (the subset doesn't use content from attributes.yaml)
    target_schema_obj.imports = [i for i in target_schema_obj.imports if i.startswith("linkml:")]

    dump_output = str(tmp_path / "biolink-profile.yaml")
    yaml_dumper.dump(target_schema_obj, dump_output)

    transformed_sv = SchemaView(dump_output)

    derived_classes = set(transformed_sv.all_classes())
    expected_classes = {
        "NamedThing",
        "Gene",
        "Disease",
        "PhenotypicFeature",
        "Association",
        "GeneToPhenotypicFeatureAssociation",
    }
    assert expected_classes <= derived_classes, f"Missing classes: {expected_classes - derived_classes}"

    derived_slots = set(transformed_sv.all_slots())
    assert "id" in derived_slots
    assert "symbol" in derived_slots
    assert "subject" in derived_slots
    assert "predicate" in derived_slots
    assert "object" in derived_slots


def test_biolink_subset_auto(biolink_schema: SchemaView, tmp_path: Path) -> None:
    """
    Test to subset the Biolink schema automatically by deriving the class definitions from biolink via a collection of class names to subset.

    :param biolink_schema: Fixture to load Biolink schema
    """
    # Initialize Session and SchemaBuilder
    session = Session()

    # Set the source schema in the session
    session.set_source_schema(biolink_schema)

    subset_classes = [
        "gene",
        "disease",
        "case to phenotypic feature association",
        "gene to disease association",
        "gene to phenotypic feature association",
        "case",
        "phenotypic feature",
    ]

    class_derivations = get_biolink_class_derivations(biolink_schema, subset_classes)
    copy_type_directives = {
        type_name: CopyDirective(element_name=type_name, copy_all=False)
        for type_name, type_def in biolink_schema.all_types().items()
    }

    ts = TransformationSpecification(
        class_derivations=class_derivations, copy_directives=copy_type_directives
    )

    mapper = SchemaMapper()
    mapper.source_schemaview = biolink_schema

    target_schema_obj = mapper.derive_schema(
        specification=ts, target_schema_id="biolink-subset", target_schema_name="BiolinkSubset"
    )

    # ugly bit of hacking to demonstrate end-to-end functionality
    target_schema_obj.types = biolink_schema.all_types()

    # Remove non-linkml imports so derived schema is standalone
    target_schema_obj.imports = [i for i in target_schema_obj.imports if i.startswith("linkml:")]

    dump_output = str(tmp_path / "biolink-subset.yaml")
    yaml_dumper.dump(target_schema_obj, dump_output)

    transformed_sv = SchemaView(dump_output)

    derived_classes = set(transformed_sv.all_classes())
    expected_classes = {
        "Gene",
        "Disease",
        "CaseToPhenotypicFeatureAssociation",
        "GeneToDiseaseAssociation",
        "GeneToPhenotypicFeatureAssociation",
        "Case",
        "PhenotypicFeature",
    }
    assert expected_classes <= derived_classes, f"Missing classes: {expected_classes - derived_classes}"

    assert len(transformed_sv.all_slots()) > 0, "Derived schema should have slots"
    assert len(transformed_sv.all_types()) > 0, "Derived schema should have types"

    gene_slots = transformed_sv.class_induced_slots("Gene")
    assert len(list(gene_slots)) > 0, "Gene class should have induced slots"
