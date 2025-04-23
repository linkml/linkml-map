"""Test conversion of normalised to denormalised schema."""

from collections.abc import Generator
from pathlib import Path

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils.schemaview import SchemaView

from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.session import Session
from src.linkml_map.utils.loaders import load_specification

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_denormalizingl(tmp_path: Generator[Path, None, None]) -> None:
    """
    Test to convert a normalized mapping set schema to a denormalized one.

    """
    input_schema = REPO_ROOT / "input/examples/flattening/source/normalized.yaml"
    # output_schema = REPO_ROOT / "input/examples/flattening/target/denormalized.yaml"
    transformation_specification_file = (
        REPO_ROOT / "input/examples/flattening/transform/denormalize.transform.yaml"
    )
    # Initialize Session and SchemaBuilder
    session = Session()

    source_schema_view = SchemaView(input_schema)
    # target_schema_view = SchemaView(output_schema)
    # Set the source schema in the session
    session.set_source_schema(source_schema_view)

    tr_spec = load_specification(transformation_specification_file)
    mapper = SchemaMapper()
    mapper.source_schemaview = source_schema_view

    target_schema_obj = mapper.derive_schema(
        specification=tr_spec,
        target_schema_id="denormalized-view",
        target_schema_name="DenormalizedView",
    )

    dump_output = str(tmp_path / "denormalized_view.yaml")
    yaml_dumper.dump(target_schema_obj, dump_output)

    transformed_sv = SchemaView(dump_output)

    for class_name in transformed_sv.all_classes():
        print(class_name)
    print()
    for slot_name in transformed_sv.all_slots():
        print(slot_name)
