import logging
from abc import ABC
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional, Union

import yaml
from curies import Converter
from linkml_runtime import SchemaView
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_transformer.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_transformer.transformer.inference import induce_missing_values

logger = logging.getLogger(__name__)


OBJECT_TYPE = Union[Dict[str, Any], BaseModel, YAMLRoot]
"""An object can be a plain python dict, a pydantic object, or a linkml YAMLRoot"""


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

    _derived_specification: TransformationSpecification = None
    """A specification with inferred missing values."""

    target_schemaview: Optional[SchemaView] = None
    """A view over the schema describing the output/target object."""

    target_module: Optional[ModuleType] = None
    """The python module which the target object should conform to."""

    prefix_map: Optional[Dict[str, str]] = None
    """Additional prefixes"""

    _curie_converter: Converter = None

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
        # self.specification = yaml_loader.load(str(path), TransformationSpecification)
        with open(path) as f:
            obj = yaml.safe_load(f)
            # necessary to expand first
            normalizer = ReferenceValidator(
                package_schemaview("linkml_transformer.datamodel.transformer_model")
            )
            normalizer.expand_all = True
            obj = normalizer.normalize(obj)
            self.specification = TransformationSpecification(**obj)

    @property
    def derived_specification(self) -> Optional[TransformationSpecification]:
        if self._derived_specification is None:
            if self.specification is None:
                return None
            self._derived_specification = deepcopy(self.specification)
            induce_missing_values(self._derived_specification, self.source_schemaview)
        return self._derived_specification

    def _get_class_derivation(self, target_class_name) -> ClassDerivation:
        spec = self.derived_specification
        matching_tgt_class_derivs = [
            deriv
            for deriv in spec.class_derivations.values()
            if deriv.populated_from == target_class_name
        ]
        logger.debug(f"Target class derivs={matching_tgt_class_derivs}")
        if len(matching_tgt_class_derivs) != 1:
            raise ValueError(f"Could not find what to derive from a source {target_class_name}")
        return matching_tgt_class_derivs[0]

    def _coerce_to_multivalued(
        self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation
    ):
        cast_as = slot_derivation.cast_collection_as
        if cast_as and cast_as == CollectionType.MultiValued:
            return True
        sv = self.target_schemaview
        if sv:
            slot = sv.induced_slot(slot_derivation.name, class_derivation.name)
            if slot.multivalued:
                return True
        return False

    def _coerce_to_singlevalued(
        self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation
    ):
        cast_as = slot_derivation.cast_collection_as
        if cast_as and cast_as == CollectionType(CollectionType.SingleValued):
            return True
        sv = self.target_schemaview
        if sv:
            slot = sv.induced_slot(slot_derivation.name, class_derivation.name)
            if not slot.multivalued:
                return True
        return False

    @property
    def curie_converter(self) -> Converter:
        if not self._curie_converter:
            self._curie_converter = Converter([])
            for prefix in self.source_schemaview.schema.prefixes.values():
                self._curie_converter.add_prefix(prefix.prefix_prefix, prefix.prefix_reference)
            for prefix in self.specification.prefixes.values():
                self._curie_converter.add_prefix(prefix.key, prefix.value)
        return self._curie_converter

    def expand_curie(self, curie: str) -> str:
        return self.curie_converter.expand(curie)

    def compress_uri(self, uri: str) -> str:
        return self.curie_converter.compress(uri)
