import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Type, Union

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import SchemaDefinition
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview

from linkml_map import ObjectTransformer
from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.inference.inverter import TransformationSpecificationInverter
from linkml_map.inference.schema_mapper import SchemaMapper
from linkml_map.transformer.transformer import Transformer

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """
    A wrapper object for a transformer session.

    TODO:

    - rename to Manager?
    - consolidate configuration
    - include source and target database

        - current spec, src_sv, tgt_sv all live in both this class and transformer
    """

    transformer_specification: Optional[TransformationSpecification] = None
    source_schemaview: Optional[SchemaView] = None
    transformer: Optional[Transformer] = None
    object_transformer: Optional[ObjectTransformer] = None
    schema_mapper: Optional[SchemaMapper] = None
    _target_schema: Optional[SchemaDefinition] = None
    _target_schemaview: Optional[SchemaView] = None

    def set_transformer_specification(
        self, specification: Optional[Union[TransformationSpecification, dict, str, Path]] = None
    ):
        if isinstance(specification, Path):
            specification = str(specification)
        if isinstance(specification, TransformationSpecification):
            self.transformer_specification = specification
        elif isinstance(specification, dict):
            # TODO: centralize this code
            normalizer = ReferenceValidator(
                package_schemaview("linkml_map.datamodel.transformer_model")
            )
            normalizer.expand_all = True
            specification = normalizer.normalize(specification)
            self.transformer_specification = TransformationSpecification(**specification)
        elif isinstance(specification, str):
            if "\n" in specification:
                obj = yaml.safe_load(specification)
            else:
                obj = yaml.safe_load(open(specification))
            self.set_transformer_specification(obj)

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

    def set_transformer(
        self,
        transformer: Optional[Union[Transformer, Type[Transformer]]],
        **kwargs,
    ):
        if isinstance(transformer, Type):
            transformer = transformer()
        transformer.specification = self.transformer_specification
        self.transformer = transformer

    def set_object_transformer(
        self,
        transformer: Optional[
            Union[ObjectTransformer, TransformationSpecification, dict, str, Path]
        ] = None,
    ):
        if transformer is None:
            if self.object_transformer is not None:
                logger.info("No change")
                return
            else:
                logger.warning("No transformer specified")
                return
        if transformer is not None:
            if isinstance(transformer, ObjectTransformer):
                self.object_transformer = transformer
            else:
                self.set_transformer_specification(transformer)
                self.object_transformer = ObjectTransformer()
                self.object_transformer.specification = self.transformer_specification
        self._target_schema = None

    @property
    def target_schema(self) -> SchemaDefinition:
        if self._target_schema is None:
            if not self.schema_mapper:
                self.schema_mapper = SchemaMapper(source_schemaview=self.source_schemaview)
            self._target_schema = self.schema_mapper.derive_schema(self.transformer_specification)
        return self._target_schema

    @property
    def target_schemaview(self) -> SchemaView:
        if self._target_schemaview is None:
            # TODO: simplify
            self._target_schemaview = SchemaView(yaml_dumper.dumps(self.target_schema))
        return self._target_schemaview

    def transform(self, obj: dict, **kwargs) -> dict:
        if self.object_transformer is None:
            raise ValueError("No transformer specified")
        if not self.object_transformer.source_schemaview:
            self.object_transformer.source_schemaview = self.source_schemaview
        return self.object_transformer.map_object(obj, **kwargs)

    def reverse_transform(self, obj: dict, **kwargs) -> dict:
        inv_spec = self.invert()
        reverse_transformer = ObjectTransformer()
        reverse_transformer.specification = inv_spec
        reverse_transformer.source_schemaview = SchemaView(yaml_dumper.dumps(self.target_schema))
        return reverse_transformer.map_object(obj, **kwargs)

    def invert(self, in_place=False) -> TransformationSpecification:
        """
        Invert the transformer specification.
        """
        inverter = TransformationSpecificationInverter(
            source_schemaview=self.source_schemaview,
            target_schemaview=SchemaView(yaml_dumper.dumps(self.target_schema)),
        )
        inv_spec = inverter.invert(self.transformer_specification)
        if in_place:
            raise NotImplementedError
        return inv_spec

    def graphviz(self, **kwargs) -> Any:
        """
        Return a graphviz representation of the schema.
        """
        from linkml_map.compiler.graphviz_compiler import GraphvizCompiler

        gc = GraphvizCompiler(source_schemaview=self.source_schemaview)
        compiled = gc.compile(self.transformer_specification)
        return compiled.digraph
