from pathlib import Path
from typing import List
from pytest import fixture

from linkml_runtime.dumpers import yaml_dumper
import pytest
from pprint import pprint
from linkml_map.datamodel.transformer_model import TransformationSpecification, ClassDerivation, SlotDerivation
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.session import Session
from linkml_runtime.utils.schemaview import SchemaView
from src.linkml_map.utils.loaders import load_specification
from linkml_map.transformer.transformer import Transformer
from linkml_map.utils.multi_file_transformer import Transformation
from linkml_model.meta import ClassDefinition
from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime.utils.formatutils import camelcase

REPO_ROOT = Path(__file__).resolve().parent.parent


@fixture
def biolink_schema():
    schema_url = "https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml"
    sv = SchemaView(schema_url)
    return sv

def test_biolink_subsetting_manual(biolink_schema):

    transform_file = REPO_ROOT / "input/examples/biolink/transform/biolink-example-profile.transform.yaml"
    # Initialize Session and SchemaBuilder
    session = Session()

    # Set the source schema in the session
    session.set_source_schema(biolink_schema)

    tr_spec = load_specification(transform_file)
    mapper = SchemaMapper()
    mapper.source_schemaview = biolink_schema

    target_schema_obj = mapper.derive_schema(specification=tr_spec,
                                             target_schema_id="biolink-profile",
                                             target_schema_name="BiolinkProfile")


    yaml_dumper.dump(target_schema_obj, str("biolink-profile.yaml"))

    transformed_sv = SchemaView("biolink-profile.yaml")

    for class_name in transformed_sv.all_classes():
        print(class_name)


def test_biolink_subset_auto(biolink_schema):
    # Initialize Session and SchemaBuilder
    session = Session()

    # Set the source schema in the session
    session.set_source_schema(biolink_schema)

    SUBSET_CLASSES = ["gene",
                      "disease",
                      "case to phenotypic feature association",
                      "gene to disease association",
                      "gene to phenotypic feature association",
                      "case",
                      "phenotypic feature",
                      ]

    class_derivations = get_biolink_class_derivations(biolink_schema, SUBSET_CLASSES)

    ts = TransformationSpecification(class_derivations=class_derivations)

    mapper = SchemaMapper()
    mapper.source_schemaview = biolink_schema

    target_schema_obj = mapper.derive_schema(specification=ts,
                                             target_schema_id="biolink-profile",
                                             target_schema_name="BiolinkProfile")

    yaml_dumper.dump(target_schema_obj, str("biolink-profile.yaml"))

    transformed_sv = SchemaView("biolink-profile.yaml")

    for class_name in transformed_sv.all_classes():
        print(class_name)



# Function to get Biolink class definitions
def get_biolink_class_derivations(sv, subset_classes) -> dict:
    # Example implementation to fetch class definitions
    # This should be replaced with the actual implementation
    class_derivations ={}
    for class_name in subset_classes:
        class_derivation = ClassDerivation(populated_from=class_name,
                                           name=camelcase(class_name))
        for slot in sv.get_class(class_name).slots:
            slot_derivation = SlotDerivation(populated_from=slot, name=camelcase(slot))
            class_derivation.slot_derivations[slot] = slot_derivation
        class_derivations[camelcase(class_name)] = class_derivation
    return class_derivations

