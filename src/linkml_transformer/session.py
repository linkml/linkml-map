import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import SchemaDefinition

from linkml_transformer import ObjectTransformer
from linkml_transformer.datamodel.transformer_model import TransformationSpecification
from linkml_transformer.inference.inverter import TransformationSpecificationInverter
from linkml_transformer.inference.schema_mapper import SchemaMapper

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """
    A wrapper object for a transformer session.
    """

    source_schemaview: Optional[SchemaView] = None
    object_transformer: Optional[ObjectTransformer] = None
    schema_mapper: Optional[SchemaMapper] = None
    _target_schema: Optional[SchemaDefinition] = None

    @property
    def transformer_specification(self) -> TransformationSpecification:
        if self.object_transformer is None:
            raise ValueError("No transformer specified")
        return self.object_transformer.specification

    def set_source_schema(self, schema: Union[str, Path, dict, SchemaView, SchemaDefinition]):
        """
        Sets the schema from a path or SchemaView object.
        """
        if isinstance(schema, str):
            sv = SchemaView(schema)
        elif isinstance(schema, Path):
            sv = SchemaView(str(schema))
        elif isinstance(schema, dict):
            sv = SchemaView(yaml_dumper.dumps(schema))
        elif isinstance(schema, SchemaView):
            sv = schema
        elif isinstance(schema, SchemaDefinition):
            sv = SchemaView(schema)
        else:
            raise ValueError(f"Unsupported schema type: {type(schema)}")
        self.source_schemaview = sv
        self._target_schema = None

    def set_object_transformer(
        self, transformer: Optional[Union[ObjectTransformer, dict, str, Path]] = None
    ):
        if transformer is None:
            if self.object_transformer is not None:
                logger.info("No change")
                return
            else:
                logger.warning("No transformer specified")
                return
        if isinstance(transformer, ObjectTransformer):
            self.object_transformer = transformer
        elif isinstance(transformer, dict):
            self.object_transformer = ObjectTransformer()
            self.object_transformer.create_transformer_specification(transformer)
        elif isinstance(transformer, str):
            self.object_transformer = ObjectTransformer()
            self.object_transformer.create_transformer_specification(yaml.safe_load(transformer))
        self._target_schema = None

    def target_schema(self) -> SchemaDefinition:
        if self._target_schema is None:
            if not self.schema_mapper:
                self.schema_mapper = SchemaMapper(source_schemaview=self.source_schemaview)
            self._target_schema = self.schema_mapper.derive_schema(
                self.object_transformer.specification
            )
        return self._target_schema

    def transform(self, obj: dict, **kwargs) -> dict:
        if self.object_transformer is None:
            raise ValueError("No transformer specified")
        if not self.object_transformer.source_schemaview:
            self.object_transformer.source_schemaview = self.source_schemaview
        return self.object_transformer.transform(obj, **kwargs)

    def reverse_transform(self, obj: dict, **kwargs) -> dict:
        inv_spec = self.invert()
        reverse_transformer = ObjectTransformer()
        reverse_transformer.specification = inv_spec
        reverse_transformer.source_schemaview = SchemaView(yaml_dumper.dumps(self.target_schema()))
        return reverse_transformer.transform(obj, **kwargs)

    def invert(self, in_place=False) -> TransformationSpecification:
        """
        Invert the transformer specification.
        """
        inverter = TransformationSpecificationInverter(
            source_schemaview=self.source_schemaview,
            target_schemaview=SchemaView(yaml_dumper.dumps(self.target_schema())),
        )
        inv_spec = inverter.invert(self.transformer_specification)
        if in_place:
            raise NotImplementedError
        return inv_spec

    def graphviz(self, **kwargs) -> Any:
        """
        Return a graphviz representation of the schema.
        """
        from linkml_transformer.compiler.graphviz_compiler import GraphvizCompiler

        gc = GraphvizCompiler(source_schemaview=self.source_schemaview)
        compiled = gc.compile(self.transformer_specification)
        return compiled.digraph
