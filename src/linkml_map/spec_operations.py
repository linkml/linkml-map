"""
Operations on a transformation specification and its source schema.

Each function takes the specification and the source schema it maps from, and returns a new artifact:
the target schema it implies, the inverse specification, or a diagram. None of them maps data; use
:class:`~linkml_map.ObjectTransformer` for that.
"""

from pathlib import Path
from typing import Any

from graphviz import Digraph
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SchemaDefinition

from linkml_map.compiler.graphviz_compiler import GraphvizCompiler
from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.inference.inverter import TransformationSpecificationInverter
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.utils.loaders import load_specification

SpecificationInput = TransformationSpecification | dict[str, Any] | Path | str
SchemaInput = SchemaView | SchemaDefinition | Path | str


def _schemaview(schema: SchemaInput) -> SchemaView:
    if isinstance(schema, SchemaView):
        return schema
    if isinstance(schema, Path):
        schema = str(schema)
    return SchemaView(schema)


def derive_schema(specification: SpecificationInput, source_schema: SchemaInput) -> SchemaDefinition:
    """
    Derive the target schema that a specification implies for a source schema.

    Equivalent to ``linkml-map derive-schema``.

    :param specification: The transformation specification, as a path, dict or loaded specification.
    :param source_schema: The schema the specification maps from, as a path or SchemaView.
    :return: The derived target schema.
    """
    return SchemaMapper(source_schemaview=_schemaview(source_schema)).derive_schema(load_specification(specification))


def invert(
    specification: SpecificationInput, source_schema: SchemaInput, strict: bool = True
) -> TransformationSpecification:
    """
    Invert a specification, so it maps the target back to the source.

    Equivalent to ``linkml-map invert``.

    :param specification: The transformation specification, as a path, dict or loaded specification.
    :param source_schema: The schema the specification maps from, as a path or SchemaView.
    :param strict: Raise when a derivation can't be inverted, instead of skipping it.
    :return: The inverse specification.
    """
    inverter = TransformationSpecificationInverter(source_schemaview=_schemaview(source_schema), strict=strict)
    return inverter.invert(load_specification(specification))


def graphviz(specification: SpecificationInput, source_schema: SchemaInput) -> Digraph:
    """
    Draw the specification as a diagram of source and target classes and the slots mapped between them.

    :param specification: The transformation specification, as a path, dict or loaded specification.
    :param source_schema: The schema the specification maps from, as a path or SchemaView.
    :return: A graphviz Digraph; render it with ``.render()`` or display it in a notebook.
    """
    compiler = GraphvizCompiler(source_schemaview=_schemaview(source_schema))
    return compiler.compile(load_specification(specification)).digraph
