"""Command line interface for linkml-map."""

import logging
import os
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import click
import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from more_itertools import chunked

from linkml_map.compiler.markdown_compiler import MarkdownCompiler
from linkml_map.compiler.python_compiler import PythonCompiler
from linkml_map.inference.inverter import TransformationSpecificationInverter
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.writers import (
    EXTENSION_FORMAT_MAP,
    MultiStreamWriter,
    OutputFormat,
    StreamWriter,
    get_stream_writer,
    make_stream_writer,
    rewrite_header_and_pad,
)

__all__ = [
    "main",
]

# CLI options
output_option = click.option("-o", "--output", help="Output file.")
schema_option = click.option("-s", "--schema", help="Path to source schema.")
transformer_specification_option = click.option(
    "-T",
    "--transformer-specification",
    multiple=True,
    help="Path to transformer specification file or directory.  Can be repeated.",
)
target_schema_option = click.option(
    "--target-schema", help="Path to target schema (required for nested object_derivations)."
)
entity_option = click.option(
    "--entity",
    help="Only process class_derivations matching this class name.",
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
@target_schema_option
@entity_option
@click.option("--source-type", help="Source type/class name for the input data.")
@click.option(
    "--unrestricted-eval/--no-unrestricted-eval",
    default=False,
    show_default=True,
    help="Allow unrestricted eval of python expressions.",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["yaml", "json", "jsonl", "tsv", "csv"]),
    default=None,
    help="Output format. Defaults to yaml for single objects, or inferred from output file extension.",
)
@click.option(
    "--chunk-size",
    type=int,
    default=1000,
    show_default=True,
    help="Number of records to process per chunk (for streaming output).",
)
@click.option(
    "-O",
    "--additional-output",
    multiple=True,
    help="Additional output files. Format inferred from extension. Can be repeated.",
)
@click.option(
    "--continue-on-error",
    is_flag=True,
    default=False,
    help="Continue processing when a row fails to transform. Report errors at end.",
)
@click.option(
    "--emit-spec",
    type=click.Path(),
    default=None,
    help="Write the resolved (merged + filtered) spec to this file path as a side-effect.",
)
@click.argument("input_data")
def map_data(
    input_data: str,
    schema: str,
    source_type: str | None,
    transformer_specification: tuple[str, ...],
    output: str | None,
    output_format: str | None,
    chunk_size: int,
    additional_output: tuple,
    continue_on_error: bool = False,
    target_schema: str | None = None,
    entity: str | None = None,
    emit_spec: str | None = None,
    **kwargs: dict[str, Any],
) -> None:
    """
    Map data from a source schema to a target schema using a transformation specification.

    INPUT_DATA can be:
      - A single YAML/JSON file (original behavior)
      - A single TSV/CSV file (each row is transformed)
      - A directory containing TSV/CSV/YAML/JSON files (multi-file transform)

    For directory input, each file should be named after the source type
    (e.g., Person.tsv for Person instances).

    Examples:
        # Single YAML file (original behavior)
        linkml-map map-data -T transform.yaml -s schema.yaml data.yaml

        # Multiple spec files merged at load time
        linkml-map map-data -T enums.yaml -T classes.yaml -s schema.yaml data/

        # Directory of spec files
        linkml-map map-data -T specs/ -s schema.yaml data/

        # Filter to a single entity class
        linkml-map map-data -T specs/ --entity Person -s schema.yaml data/

        # Multi-output: write TSV, JSON, and JSONL simultaneously
        linkml-map map-data -T transform.yaml -s schema.yaml -f jsonl -O out.tsv -O out.json input.tsv

    """
    logger.info(f"Transforming {input_data} conforming to {schema} using {transformer_specification}")

    input_path = Path(input_data)

    # Determine output format
    if output_format is None:
        if output:
            ext = Path(output).suffix.lower()
            fmt = EXTENSION_FORMAT_MAP.get(ext, OutputFormat.YAML)
            output_format = fmt.value
        else:
            output_format = "yaml"

    # Check if input is tabular or directory
    is_tabular = input_path.suffix.lower() in (".tsv", ".csv")
    is_directory = input_path.is_dir()

    if is_tabular or is_directory:
        # Use streaming transformation for tabular/directory input
        _map_data_streaming(
            input_path=input_path,
            schema=schema,
            source_type=source_type,
            transformer_specification=transformer_specification,
            output=output,
            output_format=output_format,
            chunk_size=chunk_size,
            additional_output=additional_output,
            target_schema=target_schema,
            continue_on_error=continue_on_error,
            entity=entity,
            emit_spec=emit_spec,
            **kwargs,
        )
    else:
        # Original single-object transformation
        _map_data_single(
            input_data=input_data,
            schema=schema,
            source_type=source_type,
            transformer_specification=transformer_specification,
            output=output,
            output_format=output_format,
            target_schema=target_schema,
            continue_on_error=continue_on_error,
            entity=entity,
            emit_spec=emit_spec,
            **kwargs,
        )


def _load_specs(tr: ObjectTransformer, transformer_specification: tuple[str, ...]) -> None:
    """Load one or more transformer specification files into the transformer."""
    if len(transformer_specification) == 1:
        path = Path(transformer_specification[0])
        if path.is_file():
            tr.load_transformer_specification(path)
            return
    tr.load_transformer_specifications(transformer_specification)


def _emit_spec_to_file(tr: ObjectTransformer, emit_spec: str, entity: str | None) -> None:
    """Write the resolved specification to a file, optionally filtered by entity."""
    from linkml_runtime.dumpers import yaml_dumper

    spec = tr.specification
    if entity:
        from copy import deepcopy

        spec = deepcopy(spec)
        spec.class_derivations = [cd for cd in spec.class_derivations if cd.name == entity]
    with open(emit_spec, "w", encoding="utf-8") as f:
        f.write(yaml_dumper.dumps(spec))
    logger.info("Wrote resolved spec to %s", emit_spec)


def _map_data_single(
    input_data: str,
    schema: str,
    source_type: str | None,
    transformer_specification: tuple[str, ...],
    output: str | None,
    output_format: str,
    target_schema: str | None = None,
    continue_on_error: bool = False,
    entity: str | None = None,
    emit_spec: str | None = None,
    **kwargs: dict[str, Any],
) -> None:
    """Original single-object transformation logic."""
    tr = ObjectTransformer(**kwargs)
    tr.source_schemaview = SchemaView(schema)
    _load_specs(tr, transformer_specification)
    if target_schema:
        tr.target_schemaview = SchemaView(target_schema)

    if emit_spec:
        _emit_spec_to_file(tr, emit_spec, entity)

    # Load input data (YAML or JSON)
    with open(input_data) as file:
        content = file.read()
        try:
            input_obj = yaml.safe_load(content)
        except yaml.YAMLError:
            import json

            input_obj = json.loads(content)

    tr.index(input_obj, source_type)
    try:
        tr_obj = tr.map_object(input_obj, source_type)
    except TransformationError as err:
        if not continue_on_error:
            raise
        click.echo("\n1 transformation error:", err=True)
        click.echo(f"  - {err}", err=True)
        raise SystemExit(1) from err
    dump_output(tr_obj, output_format, output)


def _build_additional_outputs(
    additional_output: tuple,
) -> list[tuple[StreamWriter, Path]]:
    """Build (StreamWriter, Path) pairs for additional -O outputs.

    :param additional_output: Tuple of file path strings from the CLI.
    :return: List of (StreamWriter, Path) tuples.
    :raises click.ClickException: If an extension cannot be mapped to a format.
    """
    result = []
    for extra_path_str in additional_output:
        extra_path = Path(extra_path_str)
        ext = extra_path.suffix.lower()
        extra_fmt = EXTENSION_FORMAT_MAP.get(ext)
        if extra_fmt is None:
            msg = f"Cannot infer output format from extension: {ext}"
            raise click.ClickException(msg)
        result.append((make_stream_writer(extra_fmt), extra_path))
    return result


def _map_data_streaming(
    input_path: Path,
    schema: str,
    source_type: str | None,
    transformer_specification: tuple[str, ...],
    output: str | None,
    output_format: str,
    chunk_size: int,
    additional_output: tuple = (),
    target_schema: str | None = None,
    continue_on_error: bool = False,
    entity: str | None = None,
    emit_spec: str | None = None,
    **kwargs: dict[str, Any],
) -> None:
    """Streaming transformation for tabular/directory input."""
    # Initialize transformer
    tr = ObjectTransformer(**kwargs)
    tr.source_schemaview = SchemaView(schema)
    _load_specs(tr, transformer_specification)
    if target_schema:
        tr.target_schemaview = SchemaView(target_schema)

    if emit_spec:
        _emit_spec_to_file(tr, emit_spec, entity)

    # Initialize data loader
    data_loader = DataLoader(input_path)

    # Set up error collection when continue-on-error is enabled
    errors: list[TransformationError] = []
    on_error = errors.append if continue_on_error else None

    # Create transform iterator and chunk it
    transform_iter = transform_spec(tr, data_loader, source_type, on_error=on_error, entity=entity)
    chunks = chunked(transform_iter, chunk_size)

    # Resolve output format
    try:
        fmt = OutputFormat(output_format)
    except ValueError:
        msg = f"Unsupported output format: {output_format}"
        raise click.ClickException(msg) from None

    if additional_output:
        extra_outputs = _build_additional_outputs(additional_output)

        # Validate no duplicate paths between primary and additional outputs
        if output:
            primary_resolved = Path(output).resolve()
            extra_paths = {p.resolve() for _, p in extra_outputs}
            if primary_resolved in extra_paths:
                msg = f"Primary output path duplicated in -O: {output}"
                raise click.ClickException(msg)

        primary_writer = make_stream_writer(fmt)
        primary_target = Path(output) if output else sys.stdout
        all_outputs = [(primary_writer, primary_target), *extra_outputs]
        MultiStreamWriter(all_outputs).write_all(chunks)
    else:
        # Original single-output path (backward compatible)
        stream_writer = get_stream_writer(fmt)

        output_ctx = open(output, "w", encoding="utf-8") if output else nullcontext(sys.stdout)
        with output_ctx as output_file:
            for chunk_str in stream_writer(chunks):
                output_file.write(chunk_str)

        # Handle header rewrite for tabular output if needed
        if output and hasattr(stream_writer, "headers"):
            logger.info("Rewriting output with updated headers")
            tmp_path = output + ".tmp"
            with open(output, encoding="utf-8") as src, open(tmp_path, "w", encoding="utf-8") as dst:
                separator = "\t" if output_format == "tsv" else ","
                for line in rewrite_header_and_pad(iter(src), stream_writer.headers, separator, chunk_size):
                    dst.write(line)
            os.replace(tmp_path, output)

    # Report collected errors
    if errors:
        click.echo(f"\n{len(errors)} transformation error(s):", err=True)
        for err in errors:
            click.echo(f"  - {err}", err=True)
        raise SystemExit(1)


@main.command()
@output_option
@transformer_specification_option
@schema_option
@click.option("--target", default="python", show_default=True, help="Target representation.")
def compile(
    schema: str,
    transformer_specification: tuple[str, ...],
    target: str,
    output: str | None,
    **kwargs: Any,
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
    _load_specs(tr, transformer_specification)
    result = compiler.compile(tr.specification)
    # dump as-is, no encoding
    dump_output(result.serialization, None, output)


@main.command()
@output_option
@transformer_specification_option
@click.argument("schema")
def derive_schema(
    schema: str,
    transformer_specification: tuple[str, ...],
    output: str | None,
    **kwargs: Any,
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
    _load_specs(tr, transformer_specification)
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
    transformer_specification: tuple[str, ...],
    output: str | None,
    **kwargs: Any,
) -> None:
    """
    Invert a transformation specification.

    Example:
        linkml-map invert -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml

    """
    logger.info(f"Inverting {transformer_specification} using {schema} as source")
    tr = ObjectTransformer()
    _load_specs(tr, transformer_specification)
    inverter = TransformationSpecificationInverter(
        source_schemaview=SchemaView(schema),
        **kwargs,
    )
    inverted_spec = inverter.invert(tr.specification)
    dump_output(inverted_spec, "yaml", output)


@main.command(name="validate-spec")
@entity_option
@click.option(
    "--merge",
    is_flag=True,
    default=False,
    help="Merge all spec files into one before validating.  Supports directories.",
)
@click.option(
    "--emit-spec",
    type=click.Path(),
    default=None,
    help="Write the resolved (merged + filtered) spec to a file path.  Use '-' for stdout.",
)
@click.argument("spec_files", nargs=-1, required=True, type=click.Path(exists=True))
def validate_spec_cmd(
    spec_files: tuple[str, ...],
    entity: str | None = None,
    merge: bool = False,
    emit_spec: str | None = None,
) -> None:
    """Validate transformation specification YAML files.

    Checks that each file conforms to the TransformationSpecification schema.
    Exits with code 1 if any file has validation errors.

    Example:

        linkml-map validate-spec my-transform.yaml

        linkml-map validate-spec specs/*.yaml

        linkml-map validate-spec --merge --entity Person --emit-spec resolved.yaml specs/
    """
    if merge:
        _validate_spec_merged(spec_files, entity=entity, emit_spec=emit_spec)
    else:
        if entity or emit_spec:
            click.echo("--entity and --emit-spec require --merge", err=True)
            raise SystemExit(1)
        _validate_spec_individual(spec_files)


def _validate_spec_individual(spec_files: tuple[str, ...]) -> None:
    """Validate each spec file independently."""
    from linkml_map.validator import validate_spec_file

    has_errors = False
    for path in spec_files:
        errors = validate_spec_file(path)
        if errors:
            has_errors = True
            click.echo(f"{path}:", err=True)
            for error in errors:
                click.echo(f"  {error}", err=True)
        else:
            click.echo(f"{path}: ok")

    if has_errors:
        raise SystemExit(1)


def _validate_spec_merged(
    spec_files: tuple[str, ...],
    entity: str | None = None,
    emit_spec: str | None = None,
) -> None:
    """Merge spec files, validate the result, optionally emit."""
    from linkml_map.utils.spec_merge import load_and_merge_specs
    from linkml_map.validator import validate_spec

    merged = load_and_merge_specs(spec_files)

    errors = validate_spec(merged)
    if errors:
        click.echo("Merged spec validation errors:", err=True)
        for error in errors:
            click.echo(f"  {error}", err=True)
        raise SystemExit(1)

    click.echo("Merged spec: ok")

    if emit_spec:
        from linkml_map.transformer.transformer import Transformer

        Transformer._normalize_spec_dict(merged)
        from linkml_map.datamodel.transformer_model import TransformationSpecification

        spec = TransformationSpecification(**merged)
        if entity:
            spec.class_derivations = [cd for cd in spec.class_derivations if cd.name == entity]
        from linkml_runtime.dumpers import yaml_dumper

        spec_yaml = yaml_dumper.dumps(spec)
        if emit_spec == "-":
            click.echo(spec_yaml)
        else:
            with open(emit_spec, "w", encoding="utf-8") as f:
                f.write(spec_yaml)
            click.echo(f"Wrote resolved spec to {emit_spec}")


def dump_output(
    output_data: dict[str, Any] | list[Any] | str,
    output_format: str | None = None,
    file_path: str | None = None,
) -> None:
    """
    Dump output to a file or stdout.

    :param output_data: data to dump
    :type output_data: dict[str, Any] | list[Any] | str
    :param output_format: format for dumped data (yaml, json, jsonl, tsv, csv)
    :type output_format: Optional[str], optional
    :param file_path: path to an output file, defaults to None
    :type file_path: Optional[str], optional
    """
    import json

    from flatten_dict import flatten
    from flatten_dict.reducers import make_reducer

    if output_data is None:
        msg = "No output to be printed"
        raise ValueError(msg)

    from linkml_map.writers.output_streams import _strip_nulls

    text_dump = output_data
    if output_format == "yaml":
        text_dump = yaml_dumper.dumps(output_data)
    elif output_format == "json":
        text_dump = json.dumps(_strip_nulls(output_data), indent=2, ensure_ascii=False) + "\n"
    elif output_format == "jsonl":
        if isinstance(output_data, list):
            text_dump = "\n".join(json.dumps(_strip_nulls(item), ensure_ascii=False) for item in output_data) + "\n"
        else:
            text_dump = json.dumps(_strip_nulls(output_data), ensure_ascii=False) + "\n"
    elif output_format in ("tsv", "csv"):
        separator = "\t" if output_format == "tsv" else ","
        reducer = make_reducer("__")
        if isinstance(output_data, list):
            rows = [flatten(item, reducer=reducer) for item in output_data]
        else:
            rows = [flatten(output_data, reducer=reducer)]
        if rows:
            headers = list(rows[0].keys())
            for row in rows[1:]:
                for k in row:
                    if k not in headers:
                        headers.append(k)
            lines = [separator.join(headers)]
            for row in rows:
                lines.append(separator.join(str(row.get(h, "")) for h in headers))
            text_dump = "\n".join(lines) + "\n"
        else:
            text_dump = ""
    elif output_format:
        msg = f"Output format {output_format} is not supported"
        raise NotImplementedError(msg)

    if not file_path:
        sys.stdout.write(text_dump)
        return

    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write(text_dump)


if __name__ == "__main__":
    main()
