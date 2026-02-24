"""
Transformers (aka data mappers) are used to transform objects from one class to another using a transformation specification.
"""

import logging
from abc import ABC
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

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
from linkml_map.utils.schema_patch import apply_schema_patch

logger = logging.getLogger(__name__)


OBJECT_TYPE = Union[dict[str, Any], BaseModel, YAMLRoot]
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

    _source_schema_patched: bool = field(default=False)
    """Flag to track if source schema patches have been applied."""

    target_schemaview: Optional[SchemaView] = None
    """A view over the schema describing the output/target object."""

    unrestricted_eval: bool = field(default=False)
    """Set to True to allow arbitrary evals as part of transformation."""

    _curie_converter: Converter = None

    def map_object(
        self, obj: OBJECT_TYPE, source_type: Optional[str] = None, **kwargs: dict[str, Any]
    ) -> OBJECT_TYPE:
        """
        Transform source object into an instance of the target class.

        :param obj:
        :param source_type:
        :return:
        """
        raise NotImplementedError

    def map_database(
        self, source_database: Any, target_database: Optional[Any] = None, **kwargs: dict[str, Any]
    ) -> OBJECT_TYPE:
        """
        Transform source resource.

        :param source_database:
        :param target_database:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def load_source_schema(self, path: Union[str, Path, dict]) -> None:
        """
        Set source_schemaview from a schema path.

        :param path:
        """
        if isinstance(path, Path):
            path = str(path)
        self.source_schemaview = SchemaView(path)

    def load_transformer_specification(self, path: Union[str, Path]) -> None:
        """
        Set specification from a schema path.

        :param path:
        :return:
        """
        with open(path) as f:
            obj = yaml.safe_load(f)
            self._normalize_spec_dict(obj)
            self.specification = TransformationSpecification(**obj)

    @classmethod
    def normalize_transform_spec(
        cls,
        obj: dict[str, Any],
        normalizer: ReferenceValidator
    ) -> dict:
        """
        Recursively normalize class_derivations and their nested object_derivations.
        """
        obj = normalizer.normalize(obj)

        class_derivations = obj.get("class_derivations", [])
        if isinstance(class_derivations, dict):
            cd_iter = class_derivations.values()
        else:
            cd_iter = class_derivations
        for class_spec in cd_iter:
            if not isinstance(class_spec, dict):
                continue
            slot_derivations = class_spec.get("slot_derivations", {})
            for slot, slot_spec in slot_derivations.items():
                # Check for nested object_derivations
                object_derivations = slot_spec.get("object_derivations", [])
                for i, od in enumerate(object_derivations):
                    # Recursively normalize each nested class_derivation block
                    od_normalized = cls.normalize_transform_spec(od, normalizer)
                    # ObjectDerivation.class_derivations stays as dict (no inlined_as_list),
                    # but the normalizer may convert it to list. Convert back.
                    od_cd = od_normalized.get("class_derivations")
                    if isinstance(od_cd, list):
                        od_normalized["class_derivations"] = {
                            item["name"]: item for item in od_cd if isinstance(item, dict)
                        }
                    object_derivations[i] = od_normalized
        return obj

    @classmethod
    def _normalize_spec_dict(cls, obj: dict[str, Any]) -> None:
        """
        Normalize a raw specification dict in place.

        Bundles _preprocess_class_derivations, ReferenceValidator normalization,
        and nested ObjectDerivation fixup into a single entry point. Mutates
        ``obj`` by replacing its contents with the normalized result.

        :param obj: Raw specification dict (e.g. from YAML or user code).
        """
        cls._preprocess_class_derivations(obj)
        normalizer = ReferenceValidator(
            package_schemaview("linkml_map.datamodel.transformer_model")
        )
        normalizer.expand_all = True
        normalized = cls.normalize_transform_spec(obj, normalizer)
        obj.clear()
        obj.update(normalized)

    @staticmethod
    def _preprocess_class_derivations(obj: dict[str, Any]) -> None:
        """
        Pre-process class_derivations before ReferenceValidator normalization.

        Handles two cases:
        1. Dict format with None values (e.g. ``Entity:`` with no body) — replace
           with empty dicts so ReferenceValidator.ensure_list doesn't choke.
        2. List format with compact keys (e.g. ``- Condition: {populated_from: x}``)
           — unwrap to ``{name: Condition, populated_from: x}`` so Pydantic can
           validate.
        """
        cd = obj.get("class_derivations")
        if isinstance(cd, dict):
            for k, v in cd.items():
                if v is None:
                    cd[k] = {}
        elif isinstance(cd, list):
            for i, item in enumerate(cd):
                # Detect YAML compact-key format: a single-key dict where the
                # key is the class name and the value is the body (dict) or
                # None.  E.g. ``- Condition: {populated_from: x}`` parses as
                # ``{"Condition": {"populated_from": "x"}}``.  We skip items
                # whose sole key is "name" — those are already in expanded
                # form (``- name: Foo``).
                if isinstance(item, dict) and len(item) == 1:
                    key, val = next(iter(item.items()))
                    if key != "name" and isinstance(val, (dict, type(None))):
                        expanded = val if val is not None else {}
                        expanded.setdefault("name", key)
                        cd[i] = expanded

    def create_transformer_specification(self, obj: dict[str, Any]) -> None:
        """
        Create specification from a dict.

        TODO: this will no longer be necessary when pydantic supports inlined as dict

        :param path:
        :return:
        """
        self._normalize_spec_dict(obj)
        self.specification = TransformationSpecification(**obj)

    def _apply_source_schema_patches(self) -> None:
        """Apply source_schema_patches from specification to source_schemaview."""
        if self._source_schema_patched:
            return
        if self.specification and self.source_schemaview:
            patches = self.specification.source_schema_patches
            if patches:
                apply_schema_patch(self.source_schemaview, patches)
                self.source_schemaview.induced_slot.cache_clear()
        self._source_schema_patched = True

    @property
    def derived_specification(self) -> Optional[TransformationSpecification]:
        if self._derived_specification is None:
            if self.specification is None:
                return None
            self._apply_source_schema_patches()
            self._derived_specification = deepcopy(self.specification)
            induce_missing_values(self._derived_specification, self.source_schemaview)
        return self._derived_specification

    def _get_class_derivation(self, target_class_name: str) -> ClassDerivation:
        spec = self.derived_specification
        matching_tgt_class_derivs = [
            deriv
            for deriv in spec.class_derivations
            if deriv.populated_from == target_class_name
            or (not deriv.populated_from and target_class_name == deriv.name)
        ]
        logger.debug(f"Target class derivations={matching_tgt_class_derivs}")
        if len(matching_tgt_class_derivs) != 1:
            msg = f"Could not find class derivation for {target_class_name} (results={len(matching_tgt_class_derivs)})"
            raise ValueError(msg)
        cd = matching_tgt_class_derivs[0]
        ancmap = self._class_derivation_ancestors(cd)
        if ancmap:
            cd = deepcopy(cd)
            for ancestor in ancmap.values():
                for k, v in ancestor.__dict__.items():
                    if v is not None and v != []:
                        curr_v = getattr(cd, k, None)
                        if isinstance(curr_v, list):
                            curr_v.extend(v)
                        elif isinstance(curr_v, dict):
                            curr_v.update({**v, **curr_v})
                        elif curr_v is None:
                            setattr(cd, k, v)
        return cd

    def _find_class_derivation_by_name(self, name: str) -> ClassDerivation:
        """Look up a class derivation by name from the specification.

        Returns the first match when multiple derivations share the same name.
        """
        for cd in self.specification.class_derivations:
            if cd.name == name:
                return cd
        msg = f"No class derivation named '{name}'"
        raise KeyError(msg)

    def _class_derivation_ancestors(self, cd: ClassDerivation) -> dict[str, ClassDerivation]:
        """
        Return a map of all class derivations that are ancestors of the given class derivation.

        :param cd:
        :return:
        """
        ancestors = {}
        parents = cd.mixins + ([cd.is_a] if cd.is_a else [])
        for parent in parents:
            parent_cd = self._find_class_derivation_by_name(parent)
            ancestors[parent] = parent_cd
            ancestors.update(self._class_derivation_ancestors(parent_cd))
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
            msg = f"Could not find what to derive from a source {target_enum_name}"
            raise ValueError(msg)
        return matching_tgt_enum_derivs[0]

    def _is_coerce_to_multivalued(
        self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation
    ) -> bool:
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
    ) -> bool:
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
        cls = cmap.get(target_range)
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
