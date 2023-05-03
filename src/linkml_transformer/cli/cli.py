"""Command line interface for linkml-transformer."""
import logging
import sys

import click

__all__ = [
    "main",
]

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper

from linkml_transformer.schema_mapper.schema_mapper import SchemaMapper
from linkml_transformer.transformer.object_transformer import ObjectTransformer

schema_option = click.option("-s", "--schema", help="Path to source schema.")
transformer_specification_option = click.option(
    "-T", "--transformer-specification", help="Path to transformer specification."
)
output_option_wb = click.option(
    "-o",
    "--output",
    type=click.File(mode="wb"),
    default=sys.stdout,
    help="Output file.",
)
output_option = click.option("-o", "--output", help="Output file.")
output_format_options = click.option(
    "-O",
    "--output-format",
    type=click.Choice(["json", "yaml", "pickle", "md"]),
    default="yaml",
    help="Output format.",
)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
# @click.version_option(__version__)
def main(verbose: int, quiet: bool):
    """CLI for linkml-transformer."""
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)
    logger.info(f"Logger {logger.name} set to level {logger.level}")


@main.command()
@output_option
@transformer_specification_option
@schema_option
@output_format_options
@click.option("--source-type")
@click.argument("input")
def map_data(
    input,
    schema,
    source_type,
    transformer_specification,
    output,
    output_format,
    **kwargs,
):
    """Map data in a source schema using a transformation."""
    logging.info(f"Transforming {input} conforming to {schema} using {transformer_specification}")
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(schema)
    tr.load_transformer_specification(transformer_specification)
    with open(input) as file:
        input_obj = yaml.safe_load(file)
    tr.index(input_obj, source_type)
    tr_obj = tr.transform(input_obj, source_type)
    if output:
        outfile = open(output, "w", encoding="utf-8")
    else:
        outfile = sys.stdout
    outfile.write(yaml_dumper.dumps(tr_obj))


@main.command()
@output_option
@transformer_specification_option
@output_format_options
@click.argument("schema")
def derive_schema(schema, transformer_specification, output, output_format, **kwargs):
    """Derive a schema from a source schema and a transformation specification.

    This can be thought of as "copying" the source to a target, using the transformation
    specification as a "patch"

    Notes:

        the implementation is currently incomplete; the derived schema may not be valid
        linkml, e.g. there may be "dangling" references.

    Example:

        linkml-tr derive-schema -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml
    """
    logging.info(f"Transforming {schema} using {transformer_specification}")
    tr = ObjectTransformer()
    tr.load_transformer_specification(transformer_specification)
    mapper = SchemaMapper(transformer=tr)
    mapper.source_schemaview = SchemaView(schema)
    target_schema = mapper.derive_schema()
    if output:
        outfile = open(output, "w", encoding="utf-8")
    else:
        outfile = sys.stdout
    outfile.write(yaml_dumper.dumps(target_schema))


if __name__ == "__main__":
    main()
