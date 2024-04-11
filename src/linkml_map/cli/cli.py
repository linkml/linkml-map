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

from linkml_map.compiler.markdown_compiler import MarkdownCompiler
from linkml_map.compiler.python_compiler import PythonCompiler
from linkml_map.inference.inverter import TransformationSpecificationInverter
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.transformer.object_transformer import ObjectTransformer

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
@click.option(
    "--unrestricted-eval/--no-unrestricted-eval",
    default=False,
    show_default=True,
    help="Allow unrestricted eval of python expressions.",
)
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
    """
    Map data from a source schema to a target schema using a transformation specification.

    Example:

        linkml-tr map-data -T X-to-Y-tr.yaml -s X.yaml  X-data.yaml
    """
    logging.info(f"Transforming {input} conforming to {schema} using {transformer_specification}")
    tr = ObjectTransformer(**kwargs)
    tr.source_schemaview = SchemaView(schema)
    tr.load_transformer_specification(transformer_specification)
    with open(input) as file:
        input_obj = yaml.safe_load(file)
    tr.index(input_obj, source_type)
    tr_obj = tr.map_object(input_obj, source_type)
    if output:
        outfile = open(output, "w", encoding="utf-8")
    else:
        outfile = sys.stdout
    outfile.write(yaml_dumper.dumps(tr_obj))


@main.command()
@output_option
@transformer_specification_option
@schema_option
@click.option("--source-type")
@click.option("--target", default="python", show_default=True, help="Target representation.")
def compile(
    schema,
    source_type,
    transformer_specification,
    target,
    output,
    **kwargs,
):
    """
    Compiles a schema to another representation.

    Example:

        linkml-tr compile -T X-to-Y-tr.yaml -s X.yaml
    """
    logging.info(f"Compiling {transformer_specification} with {schema}")
    compiler_args = {}
    if schema:
        compiler_args["source_schemaview"] = SchemaView(schema)
    if target == "python":
        compiler = PythonCompiler(**compiler_args)
    elif target == "markdown":
        compiler = MarkdownCompiler(**compiler_args)
    else:
        raise NotImplementedError(f"Compiler {target} not implemented")
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(schema)
    tr.load_transformer_specification(transformer_specification)
    result = compiler.compile(tr.specification)
    print(result.serialization)


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


@main.command()
@output_option
@transformer_specification_option
@output_format_options
@click.option("--strict/--no-strict", default=True, show_default=True, help="Strict mode.")
@click.argument("schema")
def invert(schema, transformer_specification, output, output_format, **kwargs):
    """Invert a transformation specification.

    Example:

        linkml-tr invert -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml
    """
    logging.info(f"Inverting {transformer_specification} using {schema} as source")
    tr = ObjectTransformer()
    tr.load_transformer_specification(transformer_specification)
    inverter = TransformationSpecificationInverter(
        source_schemaview=SchemaView(schema),
        **kwargs,
    )
    inverted_spec = inverter.invert(tr.specification)
    if output:
        outfile = open(output, "w", encoding="utf-8")
    else:
        outfile = sys.stdout
    outfile.write(yaml_dumper.dumps(inverted_spec))


if __name__ == "__main__":
    main()
