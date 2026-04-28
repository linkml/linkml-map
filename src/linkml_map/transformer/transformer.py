"""Transformers transform objects from one class to another using a transformation specification."""

import logging
import warnings
from abc import ABC
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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


OBJECT_TYPE = dict[str, Any] | BaseModel | YAMLRoot
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

    target_schemaview: SchemaView | None = None
    """A view over the schema describing the output/target object."""

    unrestricted_eval: bool = field(default=False)
    """Set to True to allow arbitrary evals as part of transformation."""

    _curie_converter: Converter = None

    def map_object(self, obj: OBJECT_TYPE, source_type: str | None = None, **kwargs: Any) -> OBJECT_TYPE:
        """
        Transform source object into an instance of the target class.

        :param obj:
        :param source_type:
        :return:
        """
        raise NotImplementedError

    def map_database(
        self, source_database: Any, target_database: Any | None = None, **kwargs: dict[str, Any]
    ) -> OBJECT_TYPE:
        """
        Transform source resource.

        :param source_database:
        :param target_database:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def load_source_schema(self, path: str | Path | dict) -> None:
        """
        Set source_schemaview from a schema path.

        :param path:
        """
        if isinstance(path, Path):
            path = str(path)
        self.source_schemaview = SchemaView(path)

    def load_transformer_specification(self, path: str | Path) -> None:
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
    def normalize_transform_spec(cls, obj: dict[str, Any], normalizer: ReferenceValidator) -> dict:
        """Recursively normalize class_derivations and flatten object_derivations."""
        obj = normalizer.normalize(obj)

        class_derivations = obj.get("class_derivations", [])
        if isinstance(class_derivations, dict):
            cd_iter = class_derivations.values()
        else:
            cd_iter = class_derivations
        for class_spec in cd_iter:
            if not isinstance(class_spec, dict):
                continue
            parent_source = class_spec.get("populated_from")
            slot_derivations = class_spec.get("slot_derivations", {})
            for slot_name, slot_spec in slot_derivations.items():
                if slot_spec.get("value") is not None and slot_spec.get("range") is None:
                    slot_spec["range"] = "string"
                cls._normalize_slot_class_derivations(slot_name, slot_spec, normalizer, parent_source)
        return obj

    @classmethod
    def _normalize_slot_class_derivations(
        cls,
        slot_name: str,
        slot_spec: dict[str, Any],
        normalizer: ReferenceValidator,
        parent_populated_from: str | None = None,
    ) -> None:
        """Flatten object_derivations and normalize class_derivations on a slot.

        Four steps, applied recursively to nested slots:
        1. Flatten ``object_derivations`` into ``class_derivations`` (with
           deprecation warning; error if both are present).
        2. Expand compact-key entries (``- Condition: {...}`` → ``{name: Condition, ...}``).
        3. Inherit ``populated_from`` from the parent class derivation when absent.
        4. Run the normalizer on each class derivation entry so that nested
           dict-keyed ``slot_derivations`` get ``name`` injected.
        """
        # Step 1: flatten object_derivations → class_derivations
        object_derivations = slot_spec.get("object_derivations", [])
        if object_derivations:
            if slot_spec.get("class_derivations"):
                msg = (
                    f"SlotDerivation '{slot_name}' has both 'object_derivations' and "
                    f"'class_derivations'. Remove 'object_derivations' and use "
                    f"'class_derivations' only."
                )
                raise ValueError(msg)

            warnings.warn(
                f"SlotDerivation '{slot_name}' uses 'object_derivations', which is "
                f"deprecated. Use list-based class_derivations instead. "
                f"'object_derivations' will be removed in a future version. "
                f"See https://github.com/linkml/linkml-map/issues/112",
                DeprecationWarning,
                stacklevel=4,
            )

            flattened: list[dict[str, Any]] = []
            for od in object_derivations:
                od_cd = od.get("class_derivations", {})
                if isinstance(od_cd, dict):
                    for name, body in od_cd.items():
                        entry = body if isinstance(body, dict) else {}
                        entry.setdefault("name", name)
                        flattened.append(entry)
                elif isinstance(od_cd, list):
                    flattened.extend(od_cd)
            slot_spec["class_derivations"] = flattened
            del slot_spec["object_derivations"]

        # Steps 2-4: expand compact keys, inherit populated_from, normalize, and recurse
        slot_cd = slot_spec.get("class_derivations")
        if not isinstance(slot_cd, list):
            return

        cls._expand_compact_keys(slot_cd)

        for cd_entry in slot_cd:
            if not isinstance(cd_entry, dict):
                continue
            if not cd_entry.get("populated_from") and parent_populated_from:
                cd_entry["populated_from"] = parent_populated_from
            normalized = normalizer.normalize(cd_entry)
            cd_entry.clear()
            cd_entry.update(normalized)
            child_source = cd_entry.get("populated_from")
            for nested_name, nested_sd in cd_entry.get("slot_derivations", {}).items():
                if isinstance(nested_sd, dict):
                    cls._normalize_slot_class_derivations(nested_name, nested_sd, normalizer, child_source)

    @classmethod
    def _normalize_spec_dict(cls, obj: dict[str, Any]) -> None:
        """Normalize a raw specification dict in place.

        Bundles _preprocess_class_derivations, ReferenceValidator normalization,
        and nested ObjectDerivation fixup into a single entry point. Mutates
        ``obj`` by replacing its contents with the normalized result.

        :param obj: Raw specification dict (e.g. from YAML or user code).
        """
        cls._preprocess_class_derivations(obj)
        normalizer = ReferenceValidator(package_schemaview("linkml_map.datamodel.transformer_model"))
        normalizer.expand_all = True
        normalized = cls.normalize_transform_spec(obj, normalizer)
        obj.clear()
        obj.update(normalized)

    @staticmethod
    def _expand_compact_keys(items: list[dict[str, Any]]) -> None:
        """Expand YAML compact-key dicts in a list in place.

        Converts ``{"Condition": {"populated_from": "x"}}`` →
        ``{"name": "Condition", "populated_from": "x"}``.
        Skips items whose sole key is ``"name"`` (already expanded).
        """
        for i, item in enumerate(items):
            if isinstance(item, dict) and len(item) == 1:
                key, val = next(iter(item.items()))
                if key != "name" and isinstance(val, dict | type(None)):
                    expanded = val if val is not None else {}
                    expanded.setdefault("name", key)
                    items[i] = expanded

    @staticmethod
    def _preprocess_class_derivations(obj: dict[str, Any]) -> None:
        """Pre-process top-level class_derivations before ReferenceValidator normalization.

        Handles two cases:
        1. Dict format with None values (e.g. ``Entity:`` with no body) — replace
           with empty dicts so ReferenceValidator.ensure_list doesn't choke.
        2. List format with compact keys — delegate to ``_expand_compact_keys``.
        """
        cd = obj.get("class_derivations")
        if isinstance(cd, dict):
            for k, v in cd.items():
                if v is None:
                    cd[k] = {}
        elif isinstance(cd, list):
            Transformer._expand_compact_keys(cd)

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
    def derived_specification(self) -> TransformationSpecification | None:
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
            if deriv.populated_from == target_enum_name or (not deriv.populated_from and target_enum_name == deriv.name)
        ]
        logger.debug(f"Target enum derivations={matching_tgt_enum_derivs}")
        if len(matching_tgt_enum_derivs) != 1:
            msg = f"Could not find what to derive from a source {target_enum_name}"
            raise ValueError(msg)
        return matching_tgt_enum_derivs[0]

    def _is_coerce_to_multivalued(self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation) -> bool:
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

    def _is_coerce_to_singlevalued(self, slot_derivation: SlotDerivation, class_derivation: ClassDerivation) -> bool:
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

    def _coerce_datatype(self, v: Any, target_range: str | None) -> Any:
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
