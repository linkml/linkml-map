"""Command line interface for linkml-map."""

import logging
import sys

import click

__all__ = [
    "main",
]

from typing import Any, Optional, Union

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper

from linkml_map.compiler.markdown_compiler import MarkdownCompiler
from linkml_map.compiler.python_compiler import PythonCompiler
from linkml_map.inference.inverter import TransformationSpecificationInverter
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.transformer.object_transformer import ObjectTransformer

# CLI options
output_option = click.option("-o", "--output", help="Output file.")
schema_option = click.option("-s", "--schema", help="Path to source schema.")
transformer_specification_option = click.option(
    "-T", "--transformer-specification", help="Path to transformer specification."
)

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
# @click.version_option(__version__)
def main(verbose: int, quiet: bool) -> None:
    """CLI for linkml-map."""
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
@click.option("--source-type")
@click.option(
    "--unrestricted-eval/--no-unrestricted-eval",
    default=False,
    show_default=True,
    help="Allow unrestricted eval of python expressions.",
)
@click.argument("input_data")
def map_data(
    input_data: str,
    schema: str,
    source_type: Optional[str],
    transformer_specification: str,
    output: Optional[str],
    **kwargs: dict[str, Any],
) -> None:
    """
    Map data from a source schema to a target schema using a transformation specification.

    Example:
        linkml-map map-data -T X-to-Y-tr.yaml -s X.yaml  X-data.yaml

    """
    logger.info(
        f"Transforming {input_data} conforming to {schema} using {transformer_specification}"
    )
    tr = ObjectTransformer(**kwargs)
    tr.source_schemaview = SchemaView(schema)
    tr.load_transformer_specification(transformer_specification)
    with open(input_data) as file:
        input_obj = yaml.safe_load(file)
    tr.index(input_obj, source_type)
    tr_obj = tr.map_object(input_obj, source_type)
    dump_output(tr_obj, "yaml", output)


@main.command()
@output_option
@transformer_specification_option
@schema_option
@click.option("--target", default="python", show_default=True, help="Target representation.")
def compile(
    schema: str,
    transformer_specification: str,
    target: str,
    output: Optional[str],
    **kwargs: Optional[dict[str, Any]],
) -> None:
    """
    Compiles a schema to another representation.

    Example:
        linkml-map compile -T X-to-Y-tr.yaml -s X.yaml

    """
    logger.info(f"Compiling {transformer_specification} with {schema}")
    sv = SchemaView(schema)
    compiler_args = {"source_schemaview": sv}
    if target == "python":
        compiler = PythonCompiler(**compiler_args)
    elif target == "markdown":
        compiler = MarkdownCompiler(**compiler_args)
    else:
        msg = f"Compiler {target} not implemented"
        raise NotImplementedError(msg)
    tr = ObjectTransformer()
    tr.source_schemaview = sv
    tr.load_transformer_specification(transformer_specification)
    result = compiler.compile(tr.specification)
    # dump as-is, no encoding
    dump_output(result.serialization, None, output)


@main.command()
@output_option
@transformer_specification_option
@click.argument("schema")
def derive_schema(
    schema: str,
    transformer_specification: str,
    output: Optional[str],
    **kwargs: Optional[dict[str, Any]],
) -> None:
    """
    Derive a schema from a source schema and a transformation specification.

    This can be thought of as "copying" the source to a target, using the transformation
    specification as a "patch"

    Notes:
        the implementation is currently incomplete; the derived schema may not be valid
        linkml, e.g. there may be "dangling" references.

    Example:
        linkml-map derive-schema -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml

    """
    logger.info(f"Transforming {schema} using {transformer_specification}")
    tr = ObjectTransformer()
    tr.load_transformer_specification(transformer_specification)
    mapper = SchemaMapper(transformer=tr)
    mapper.source_schemaview = SchemaView(schema)
    target_schema = mapper.derive_schema()
    dump_output(target_schema, "yaml", output)


@main.command()
@output_option
@transformer_specification_option
@click.option("--strict/--no-strict", default=True, show_default=True, help="Strict mode.")
@click.argument("schema")
def invert(
    schema: str,
    transformer_specification: str,
    output: Optional[str],
    **kwargs: Optional[dict[str, Any]],
) -> None:
    """
    Invert a transformation specification.

    Example:
        linkml-map invert -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml

    """
    logger.info(f"Inverting {transformer_specification} using {schema} as source")
    tr = ObjectTransformer()
    tr.load_transformer_specification(transformer_specification)
    inverter = TransformationSpecificationInverter(
        source_schemaview=SchemaView(schema),
        **kwargs,
    )
    inverted_spec = inverter.invert(tr.specification)
    dump_output(inverted_spec, "yaml", output)


def dump_output(
    output_data: Union[dict[str, Any], list[Any], str],
    output_format: Optional[str] = None,
    file_path: Optional[str] = None,
) -> None:
    """
    Dump output as YAML to a file or stdout.

    :param output_data: data to dump
    :type output_data: dict[str, Any] | list[Any] | str
    :param output_format: format for dumped data, defaults to None
    :type output_format: Optional[str], optional
    :param file_path: path to an output file, defaults to None
    :type file_path: Optional[str], optional
    """
    if output_data is None:
        # this should already have been caught...
        msg = "No output to be printed"
        raise ValueError(msg)

    text_dump = output_data
    if output_format == "yaml":
        text_dump = yaml_dumper.dumps(output_data)
    elif output_format:
        # some other defined output format
        msg = f"Output format {output_format} is not supported"
        raise NotImplementedError(msg)

    if not file_path:
        sys.stdout.write(text_dump)
        return

    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write(text_dump)


if __name__ == "__main__":
    main()
