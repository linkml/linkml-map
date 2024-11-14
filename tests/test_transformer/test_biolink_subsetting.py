from pathlib import Path

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils.formatutils import camelcase, underscore
from linkml_runtime.utils.schemaview import SchemaView
from pytest import fixture

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    SlotDerivation,
    TransformationSpecification,
    CopyDirective
)
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.session import Session
from src.linkml_map.utils.loaders import load_specification

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_biolink_class_derivations(sv, subset_classes) -> dict:
    """
    Function to get Biolink class definitions

    :param sv: SchemaView object
    :param subset_classes: List of classes to subset
    :return: Dictionary of class derivations incl slot derivations
    """
    # Example implementation to fetch class definitions
    # This should be replaced with the actual implementation
    class_derivations = {}
    for class_name in subset_classes:
        class_derivation = ClassDerivation(populated_from=class_name, name=camelcase(class_name))
        induced_slots = sv.class_induced_slots(class_name)
        for slot in induced_slots:
            slot_derivation = SlotDerivation(populated_from=slot.name, name=underscore(slot.name))
            class_derivation.slot_derivations[underscore(slot.name)] = slot_derivation
        class_derivations[camelcase(class_name)] = class_derivation
    return class_derivations


@fixture
def biolink_schema():
    """
    Fixture to load Biolink schema

    :return: SchemaView object named `biolink-schema`
    """

    schema_url = "https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml"
    sv = SchemaView(schema_url)
    return sv


def test_biolink_subsetting_manual(biolink_schema):
    """
    Test to subset the Biolink schema manually

    :param biolink_schema: Fixture to load Biolink schema
    """
    transform_file = (
        REPO_ROOT / "input/examples/biolink/transform/biolink-example-profile.transform.yaml"
    )
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

    yaml_dumper.dump(target_schema_obj, str("biolink-profile.yaml"))

    transformed_sv = SchemaView("biolink-profile.yaml")

    for class_name in transformed_sv.all_classes():
        print(class_name)
    print()
    for slot_name in transformed_sv.all_slots():
        print(slot_name)


def test_biolink_subset_auto(biolink_schema):
    """
    Test to subset the Biolink schema automatically by deriving the class definitions from biolink
    via a collection of class names to subset.

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
    copy_type_directive = {
        type_name: CopyDirective(element_name=type_name, copy_all=True)
        for type_name, type_def in biolink_schema.all_types().items()
    }
    ts = TransformationSpecification(class_derivations=class_derivations, )

    mapper = SchemaMapper()
    mapper.source_schemaview = biolink_schema

    target_schema_obj = mapper.derive_schema(
        specification=ts, target_schema_id="biolink-profile", target_schema_name="BiolinkProfile"
    )

    yaml_dumper.dump(target_schema_obj, str("biolink-subset.yaml"))

    transformed_sv = SchemaView("biolink-subset.yaml")

    for class_name in transformed_sv.all_classes():
        print(class_name)
    print()
    for slot_name in transformed_sv.all_slots():
        print(slot_name)
