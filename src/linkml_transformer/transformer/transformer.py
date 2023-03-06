import logging
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional, Type, Union

from linkml_runtime import SchemaView
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_transformer.datamodel.transformer_model import (
    ClassDerivation, TransformationSpecification)

logger = logging.getLogger(__name__)


OBJECT_TYPE = Union[Dict[str, Any], BaseModel, YAMLRoot]


@dataclass
class Transformer(ABC):
    """
    Base class for all transformers.

    A transformer will generate an instance of a target class from
    an instance of a source class, making use of a specification.

    This is an abstract class. Different implementations will
    subclass this
    """

    source_schemaview: SchemaView = None
    """A view over the schema describing the input/source object."""

    specification: TransformationSpecification = None
    """A specification of how to generate target objects from source objects."""

    target_schemaview: Optional[SchemaView] = None
    """A view over the schema describing the output/target object."""

    target_module: Optional[ModuleType] = None
    """The python module which the target object should conform to."""

    def transform(self, obj: OBJECT_TYPE, source_type: str = None) -> OBJECT_TYPE:
        """
        Transform source object into an instance of the target class.

        :param obj:
        :param source_type:
        :return:
        """
        raise NotImplementedError

    def load_source_schema(self, path: Union[str, Path]):
        """
        Sets source_schemaview from a schema path.

        :param path:
        :return:
        """
        self.source_schemaview = SchemaView(str(path))

    def load_transformer_specification(self, path: Union[str, Path]):
        """
        Sets specification from a schema path.

        :param path:
        :return:
        """
        self.specification = yaml_loader.load(str(path), TransformationSpecification)

    def _get_class_derivation(self, target_class_name) -> ClassDerivation:
        spec = self.specification
        matching_tgt_class_derivs = [
            deriv
            for deriv in spec.class_derivations.values()
            if deriv.populated_from == target_class_name
        ]
        logger.debug(f"Target class derivs={matching_tgt_class_derivs}")
        if len(matching_tgt_class_derivs) != 1:
            raise ValueError(
                f"Could not find what to derive from a source {target_class_name}"
            )
        return matching_tgt_class_derivs[0]
