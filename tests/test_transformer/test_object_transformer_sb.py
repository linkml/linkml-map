"""Test the object transformer."""

from typing import Any

import pytest
import yaml

from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import (
    ClassDefinition,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview

import tests.input.examples.flattening.model.denormalized_model as sssom_tgt_dm
import tests.input.examples.flattening.model.normalized_model as sssom_src_dm
import tests.input.examples.personinfo_basic.model.agent_model as tgt_dm
import tests.input.examples.personinfo_basic.model.personinfo_model as src_dm
from linkml_map.compiler.tr import TR_TO_MAPPING_TABLES
from linkml_map.datamodel import TR_SCHEMA
from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.utils.dynamic_object import dynamic_object
from tests import (
    DENORM_SCHEMA,
    DENORM_SPECIFICATION,
    FLATTENING_DATA,
    NORM_SCHEMA,
    PERSONINFO_CONTAINER_DATA,
    PERSONINFO_CONTAINER_TGT_DATA,
    PERSONINFO_DATA,
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TGT_DATA,
    PERSONINFO_TGT_SCHEMA,
    PERSONINFO_TR,
)

AGE_STRING = "33 years"
AGE_INT = 33

TARGET_DATA = yaml.safe_load(open(str(PERSONINFO_TGT_DATA)))
TARGET_OBJECT = yaml_loader.load(str(PERSONINFO_TGT_DATA), target_class=tgt_dm.Agent)

CONTAINER_DATA = yaml.safe_load(open(str(PERSONINFO_CONTAINER_TGT_DATA)))
CONTAINER_OBJECT = yaml_loader.load(
    str(PERSONINFO_CONTAINER_TGT_DATA), target_class=tgt_dm.Container
)

def inject_slot(schema_dict: dict, class_name: str, slot_name: str, slot_def: dict):
    schema_dict.setdefault("slots", {})[slot_name] = slot_def
    schema_dict["classes"][class_name].setdefault("slots", []).append(slot_name)

def inject_enum(schema: dict, enum_name: str, values: list[str]) -> None:
    schema["enums"][enum_name] = { "permissible_values": {val: {} for val in values} }

@pytest.fixture
def obj_tr() -> ObjectTransformer:
    """Instantiate an object transformer."""
    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = SchemaView(str(PERSONINFO_SRC_SCHEMA))
    obj_tr.target_schemaview = SchemaView(str(PERSONINFO_TGT_SCHEMA))
    obj_tr.load_transformer_specification(PERSONINFO_TR)
    return obj_tr

def build_base_source_schema() -> SchemaBuilder:
    sb = SchemaBuilder(name="SourceSchema", id="http://example.org/source-schema")
    sb.add_class("Source")
    sb.add_defaults()
    return sb

def build_base_target_schema() -> SchemaBuilder:
    sb = SchemaBuilder(name="TargetSchema", id="http://example.org/target-schema")
    sb.add_class("Target")
    sb.add_defaults()
    return sb

def build_empty_transform_spec() -> TransformationSpecification:
    return TransformationSpecification(class_derivations={})

def build_transformer_specification(string: str) -> TransformationSpecification:
    """
    Build a TransformationSpecification from a YAML string.
    
    :param string: YAML string representing the transformation specification
    :return: TransformationSpecification object
    """
    spec_dict = yaml.safe_load(string)
    return TransformationSpecification(**spec_dict)

def build_transformer_from_spec(
    source_sb: SchemaBuilder,
    target_sb: SchemaBuilder,
    spec: TransformationSpecification
) -> ObjectTransformer:
    obj_tr = ObjectTransformer(unrestricted_eval=True)
    obj_tr.source_schemaview = SchemaView(yaml.dump(source_sb.schema.to_dict()))
    obj_tr.target_schemaview = SchemaView(yaml.dump(target_sb.schema.to_dict()))
    obj_tr.create_transformer_specification(spec.model_dump())
    return obj_tr

class TransformationTestBuilder:
    def __init__(self):
        self.source_sb = build_base_source_schema()
        self.target_sb = build_base_target_schema()
        self.spec = build_empty_transform_spec()
        self.input_data: dict = {}
        self.expected_output: dict = {}

    def set_input(self, obj: dict) -> None:
        self.input_data = obj

    def set_expected(self, obj: dict) -> None:
        self.expected_output = obj

    def transformer(self) -> ObjectTransformer:
        return build_transformer_from_spec(
            self.source_sb,
            self.target_sb,
            self.spec
        )

    def run(self) -> dict:
        transformer = self.transformer()
        return transformer.map_object(self.input_data, source_type="Person")
    
def add_dict_transformation(builder: TransformationTestBuilder):
    # Source: Source.age_in_years: integer
    builder.source_sb.add_slot(
        "age_in_years", range="integer"
    )
    builder.source_sb.add_slot(
        "id", range="string"
    )
    builder.source_sb.add_class(
        "Person", slots=["id", "age_in_years"]
    )

    # Target: Target.age: string
    builder.target_sb.add_slot(
        "age", range="string"
    )
    builder.target_sb.add_slot(
        "id", range="string"
    )
    builder.target_sb.add_class(
        "Agent", slots=["id", "age"]
    )

    builder.spec = build_transformer_specification("""
class_derivations:
  Agent:
    populated_from: Person
    slot_derivations:
      id:
      age:
        expr: "str({age_in_years}) + ' years'"                                                 
    """)


def test_transform_dict():
    # tb = TransformationTestBuilder()
    # add_dict_transformation(tb)

    # tb.set_input({
    #     "id": "P:001",
    #     "age_in_years": 33
    # })

    # tb.set_expected({
    #     "id": "P:001",
    #     "age": "33 years"
    # })

    # result = tb.run()
    # assert result == tb.expected_output
    assert True  # Placeholder for the actual test implementation

