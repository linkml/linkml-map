from pathlib import Path
from linkml_runtime.dumpers import yaml_dumper
import pytest
from pprint import pprint
from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.session import Session
from linkml_runtime.utils.schemaview import SchemaView
from src.linkml_map.utils.loaders import load_specification
from linkml_map.transformer.transformer import Transformer
from linkml_map.utils.multi_file_transformer import Transformation




def test_biolink_subsetting():
    # Test that the subsetting of the Biolink Model is correct
    # This test is a placeholder and should be replaced with a real test
    repo_root = Path(__file__).resolve().parent.parent
    schema_url = "https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml"
    sv = SchemaView(schema_url)

    transform_file = repo_root / "input/examples/biolink/transform/biolink-example-profile.transform.yaml"
    # Initialize Session and SchemaBuilder
    session = Session()

    # Set the source schema in the session
    session.set_source_schema(sv)

    SUBSET_CLASSES = ["gene",
                      "disease",
                      "case to phenotypic feature association",
                      "gene to disease association",
                      "gene to phenotypic feature association",
                      "case",
                      "phenotypic feature",
                      ]


    tr_spec = load_specification(transform_file)
    mapper = SchemaMapper()
    mapper.source_schemaview = sv

    target_schema_obj = mapper.derive_schema(specification=tr_spec,
                                             target_schema_id="biolink-profile",
                                             target_schema_name="BiolinkProfile")

    yaml_dumper.dump(target_schema_obj, str("biolink-profile.yaml"))
