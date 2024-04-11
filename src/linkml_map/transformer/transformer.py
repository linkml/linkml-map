"""
Transformers (aka data mappers) are used to transform objects from one class to another
using a transformation specification.
"""

import logging
from abc import ABC
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from curies import Converter
from linkml_runtime import SchemaView
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    EnumDerivation,
    SlotDerivation,
    TransformationSpecification,
)
from linkml_map.inference.inference import induce_missing_values

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

    specification: TransformationSpecification = None
    """A specification of how to generate target objects from source objects."""

    source_schemaview: SchemaView = None
    """A view over the schema describing the input/source object."""

    _derived_specification: TransformationSpecification = None
    """A specification with inferred missing values."""

    target_schemaview: Optional[SchemaView] = None
    """A view over the schema describing the output/target object."""

    unrestricted_eval: bool = field(default=False)
    """Set to True to allow arbitrary evals as part of transformation."""

    _curie_converter: Converter = None

    def map_object(self, obj: OBJECT_TYPE, source_type: str = None, **kwargs) -> OBJECT_TYPE:
        """
        Transform source object into an instance of the target class.

        :param obj:
        :param source_type:
        :return:
        """
        raise NotImplementedError

    def map_database(
        self, source_database: Any, target_database: Optional[Any] = None, **kwargs
    ) -> OBJECT_TYPE:
        """
        Transform source resource.

        :param source_database:
        :param target_database:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def load_source_schema(self, path: Union[str, Path, dict]):
        """
        Sets source_schemaview from a schema path.

        :param path:
        :return:
        """
        if isinstance(path, Path):
            path = str(path)
        self.source_schemaview = SchemaView(path)

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
                package_schemaview("linkml_map.datamodel.transformer_model")
            )
            normalizer.expand_all = True
            obj = normalizer.normalize(obj)
            self.specification = TransformationSpecification(**obj)

    def create_transformer_specification(self, obj: Dict[str, Any]):
        """
        Creates specification from a dict.

        TODO: this will no longer be necessary when pydantic supports inlined as dict

        :param path:
        :return:
        """
        normalizer = ReferenceValidator(
            package_schemaview("linkml_map.datamodel.transformer_model")
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

    def _get_class_derivation(self, target_class_name: str) -> ClassDerivation:
        spec = self.derived_specification
        matching_tgt_class_derivs = [
            deriv
            for deriv in spec.class_derivations.values()
            if deriv.populated_from == target_class_name
            or (not deriv.populated_from and target_class_name == deriv.name)
        ]
        logger.debug(f"Target class derivations={matching_tgt_class_derivs}")
        if len(matching_tgt_class_derivs) != 1:
            raise ValueError(
                f"Could not find class derivation for {target_class_name} (results={len(matching_tgt_class_derivs)})"
            )
        cd = matching_tgt_class_derivs[0]
        ancmap = self._class_derivation_ancestors(cd)
        if ancmap:
            cd = deepcopy(cd)
            for anc in ancmap.values():
                for k, v in anc.__dict__.items():
                    if v is not None and v != []:
                        curr_v = getattr(cd, k, None)
                        if isinstance(curr_v, list):
                            curr_v.extend(v)
                        elif isinstance(curr_v, dict):
                            curr_v.update({**v, **curr_v})
                        else:
                            if curr_v is None:
                                setattr(cd, k, v)
        return cd

    def _class_derivation_ancestors(self, cd: ClassDerivation) -> Dict[str, ClassDerivation]:
        """
        Returns a map of all class derivations that are ancestors of the given class derivation.
        :param cd:
        :return:
        """
        spec = self.specification
        ancestors = {}
        parents = cd.mixins + ([cd.is_a] if cd.is_a else [])
        for parent in parents:
            ancestors[parent] = spec.class_derivations[parent]
            ancestors.update(self._class_derivation_ancestors(spec.class_derivations[parent]))
        return ancestors

    def _get_enum_derivation(self, target_enum_name: str) -> EnumDerivation:
        spec = self.derived_specification
        matching_tgt_enum_derivs = [
            deriv
            for deriv in spec.enum_derivations.values()
            if deriv.populated_from == target_enum_name
            or (not deriv.populated_from and target_enum_name == deriv.name)
        ]
        logger.debug(f"Target enum derivations={matching_tgt_enum_derivs}")
        if len(matching_tgt_enum_derivs) != 1:
            raise ValueError(f"Could not find what to derive from a source {target_enum_name}")
        return matching_tgt_enum_derivs[0]

    def _is_coerce_to_multivalued(
        self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation
    ):
        cast_as = slot_derivation.cast_collection_as
        if cast_as and cast_as in [
            CollectionType.MultiValued,
            CollectionType.MultiValuedDict,
            CollectionType.MultiValuedDict,
        ]:
            return True
        if slot_derivation.stringification and slot_derivation.stringification.reversed:
            return True
        sv = self.target_schemaview
        if sv:
            slot = sv.induced_slot(slot_derivation.name, class_derivation.name)
            if slot.multivalued:
                return True
        return False

    def _is_coerce_to_singlevalued(
        self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation
    ):
        cast_as = slot_derivation.cast_collection_as
        if cast_as and cast_as == CollectionType(CollectionType.SingleValued):
            return True
        if slot_derivation.stringification and not slot_derivation.stringification.reversed:
            return True
        sv = self.target_schemaview
        if sv:
            slot = sv.induced_slot(slot_derivation.name, class_derivation.name)
            if not slot.multivalued:
                return True
        return False

    def _coerce_datatype(self, v: Any, target_range: Optional[str]) -> Any:
        if target_range is None:
            return v
        if isinstance(v, list):
            return [self._coerce_datatype(v1, target_range) for v1 in v]
        if isinstance(v, dict):
            return {k: self._coerce_datatype(v1, target_range) for k, v1 in v.items()}
        cmap = {
            "integer": int,
            "float": float,
            "string": str,
            "boolean": bool,
        }
        cls = cmap.get(target_range, None)
        if not cls:
            logger.warning(f"Unknown target range {target_range}")
            return v
        if isinstance(v, cls):
            return v
        return cls(v)

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
