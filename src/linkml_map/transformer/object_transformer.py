"""A Transformer that works on in-memory dict objects."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Optional, Union

import yaml
from asteval import Interpreter
from linkml_runtime import SchemaView
from linkml_runtime.index.object_index import ObjectIndex
from linkml_runtime.linkml_model import SlotDefinition
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    PivotDirectionType,
    PivotOperation,
    SerializationSyntaxType,
    SlotDerivation,
)
from linkml_map.functions.unit_conversion import UnitSystem, convert_units
from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.transformer import OBJECT_TYPE, Transformer
from linkml_map.utils.dynamic_object import DynObj, dynamic_object
from linkml_map.utils.eval_utils import _uuid5, eval_expr, eval_expr_with_mapping
from linkml_map.utils.fk_utils import FKResolution, resolve_fk_path

DICT_OBJ = dict[str, Any]


logger = logging.getLogger(__name__)


class Bindings(Mapping):
    """
    Efficiently access source object attributes.
    """

    def __init__(  # noqa: PLR0913
        self,
        object_transformer: ObjectTransformer,
        source_obj: OBJECT_TYPE,
        source_obj_typed: OBJECT_TYPE,
        source_type: str,
        sv: SchemaView,
        bindings: dict,
        class_deriv: Optional[ClassDerivation] = None,
    ) -> None:
        self.object_transformer: ObjectTransformer = object_transformer
        self.source_obj: OBJECT_TYPE = source_obj
        self.source_obj_typed: OBJECT_TYPE = source_obj_typed
        self.source_type: str = source_type
        self.sv: SchemaView = sv
        self.bindings: dict = {}
        self.class_deriv: Optional[ClassDerivation] = class_deriv
        if bindings:
            self.bindings.update(bindings)

    @classmethod
    def from_context(cls, transformer: ObjectTransformer, context: DerivationContext) -> Bindings:
        """Create Bindings from a DerivationContext."""
        return cls(
            transformer,
            source_obj=context.source_obj,
            source_obj_typed=context.source_obj_typed,
            source_type=context.source_type,
            sv=context.sv,
            bindings={"NULL": None},
            class_deriv=context.class_deriv,
        )

    def get_ctxt_obj_and_dict(self, source_obj: OBJECT_TYPE = None) -> tuple[DynObj, OBJECT_TYPE]:
        """
        Transform a source object into a typed context object and dictionary, and cache results.

        :param source_obj: Source data. Should be a subset of source_obj provided in the constructor.
        If None the full source_obj from constructor is used.
        :return: Tuple of typed context object and context dictionary. The object is the dictionary
        with keys converted to member variables.
        """
        if source_obj is None:
            source_obj = self.source_obj

        if self.object_transformer.object_index:
            if not self.source_obj_typed:
                source_obj_dyn = dynamic_object(source_obj, self.sv, self.source_type)
            else:
                source_obj_dyn = self.source_obj_typed
            # Clear cache: Cache doesn't work since the cache key is the same when source_obj has only a subset
            # of its keys. eg. {"age": self.source_obj["age"]} and {"name": self.source_obj["name"]}
            # (with optionally the identifier key included) will have the same cache key, and so `bless` will
            # incorrectly return the same cached values.
            self.object_transformer.object_index.clear_proxy_object_cache()

            ctxt_obj = self.object_transformer.object_index.bless(source_obj_dyn)
            ctxt_dict = {k: getattr(ctxt_obj, k) for k in ctxt_obj._attributes() if not k.startswith("_")}
        else:
            do = dynamic_object(source_obj, self.sv, self.source_type)
            ctxt_obj = do
            ctxt_dict = vars(do)

        self.bindings.update(ctxt_dict)

        return ctxt_obj, ctxt_dict

    def _all_keys(self) -> list[Any]:
        keys = list(self.source_obj.keys()) + list(self.bindings.keys())
        # Remove duplicate keys (ie. found in both source_obj and bindings), and retain original order
        return list(dict.fromkeys(keys).keys())

    def __len__(self) -> int:
        return len(self._all_keys())

    def __iter__(self) -> Iterator:
        return iter(self._all_keys())

    @property
    def _join_specs(self) -> dict:
        """Active join specs from the class derivation, or empty dict."""
        if self.class_deriv and self.class_deriv.joins:
            return self.class_deriv.joins
        return {}

    def __getitem__(self, name: Any) -> Any:
        if name not in self.bindings:
            if name in self._join_specs:
                self.bindings[name] = self._resolve_join(name)
            else:
                _ = self.get_ctxt_obj_and_dict({name: self.source_obj[name]})

        return self.bindings.get(name)

    def _resolve_join(self, table_name: str) -> Optional[DynObj]:
        """Resolve a cross-table lookup, returning a DynObj or None."""
        row = self.object_transformer._resolve_joined_row(table_name, self.source_obj, self.class_deriv)
        if row is None:
            return None
        return DynObj(**row)

    def __setitem__(self, name: Any, value: Any) -> None:
        del name, value
        msg = f"__setitem__ not allowed on class {self.__class__.__name__}"
        raise RuntimeError(msg)


@dataclass(frozen=True)
class DerivationContext:
    """Immutable context for slot derivation within a single map_object call."""

    source_obj: DICT_OBJ
    source_obj_typed: Optional[Any]
    source_type: str
    sv: SchemaView
    class_deriv: ClassDerivation


@dataclass
class ObjectTransformer(Transformer):
    """
    A Transformer that works on in-memory dict objects.

    This works recursively
    """

    object_index: ObjectIndex = None
    lookup_index: Any = None  # Optional[LookupIndex] — lazy import to avoid hard duckdb dep

    def index(self, source_obj: Any, target: Optional[str] = None) -> None:
        """
        Create an index over a container object.

        :param source_obj: source data structure to be indexed
        :param target: class to convert source object into
        """
        if isinstance(source_obj, dict):
            if target is None:
                [target] = [c.name for c in self.source_schemaview.all_classes().values() if c.tree_root]
            if target is None:
                msg = f"target must be passed if source_obj is dict: {source_obj}"
                raise ValueError(msg)
            source_obj_typed = dynamic_object(source_obj, self.source_schemaview, target)
            self.object_index = ObjectIndex(source_obj_typed, schemaview=self.source_schemaview)
        else:
            self.object_index = ObjectIndex(source_obj, schemaview=self.source_schemaview)

    def _resolve_source_type(self, source_type: Optional[str], sv: Optional[SchemaView]) -> Optional[str]:
        """
        Resolve the source type when not explicitly provided.

        :param source_type: Explicitly provided source type, or None.
        :param sv: Source schema view, may be None.
        :return: Resolved source type name.
        """
        if source_type is None and sv is None:
            # TODO: use smarter method
            if self.specification.class_derivations:
                source_type = self.specification.class_derivations[0].name
            else:
                msg = (
                    "Cannot resolve source type: no source_type provided, "
                    "no SchemaView available, and specification has no class_derivations"
                )
                raise ValueError(msg)
        if source_type is None and sv is not None:
            source_types = [c.name for c in sv.all_classes().values() if c.tree_root]
            if len(source_types) == 1:
                source_type = source_types[0]
            elif len(source_types) > 1:
                msg = "No source type specified and multiple root classes found"
                raise ValueError(msg)
            elif len(source_types) == 0:
                if len(sv.all_classes()) == 1:
                    source_type = next(iter(sv.all_classes().keys()))
                else:
                    msg = "No source type specified and no root classes found"
                    raise ValueError(msg)
        return source_type

    def map_object(
        self,
        source_obj: OBJECT_TYPE,
        source_type: Optional[str] = None,
        target_type: Optional[str] = None,
        class_derivation: Optional[ClassDerivation] = None,
    ) -> Union[DICT_OBJ, Any]:
        """
        Transform a source object into a target object.

        :param source_obj: source data structure
        :param source_type: source_obj instantiates this (may be class, type, or enum)
        :param target_type: target_obj instantiates this (may be class, type, or enum)
        :return: transformed data, either as type target_type or a dictionary
        """
        sv = self.source_schemaview
        source_type = self._resolve_source_type(source_type, sv)

        if source_type in sv.all_types():
            if target_type:
                if target_type == "string":
                    return str(source_obj)
                if target_type == "integer":
                    return int(source_obj)
                if target_type in {"float", "double"}:
                    return float(source_obj)
                if target_type == "uri":
                    return self.expand_curie(source_obj)
                if target_type == "curie":
                    return self.compress_uri(source_obj)
            return source_obj
        if source_type in sv.all_enums():
            return self.transform_enum(source_obj, [source_type], source_obj)

        source_obj_typed = None
        if isinstance(source_obj, (BaseModel, YAMLRoot)):
            # ensure dict
            source_obj_typed = source_obj
            source_obj = vars(source_obj)
        if not isinstance(source_obj, dict):
            logger.warning(f"Unexpected: {source_obj} for type {source_type}")
            return source_obj
        class_deriv = class_derivation or self._get_class_derivation(source_type)

        # Handle class-level pivot operations (UNMELT from EAV to wide format)
        if class_deriv.pivot_operation:
            return self._perform_pivot_operation(class_deriv.pivot_operation, source_obj, class_deriv, sv, source_type)

        context = DerivationContext(
            source_obj=source_obj,
            source_obj_typed=source_obj_typed,
            source_type=source_type,
            sv=sv,
            class_deriv=class_deriv,
        )
        tgt_attrs = {}
        bindings = None
        # map each slot assignment in source_obj, if there is a slot_derivation
        for slot_derivation in class_deriv.slot_derivations.values():
            try:
                v = None
                source_class_slot = None
                if slot_derivation.value is not None:
                    v = slot_derivation.value
                elif slot_derivation.unit_conversion:
                    v = self._perform_unit_conversion(slot_derivation, context)
                elif slot_derivation.pivot_operation:
                    # MELT operation: wide format to EAV/long format
                    v = self._perform_melt(slot_derivation.pivot_operation, source_obj, slot_derivation)
                elif slot_derivation.expr:
                    if bindings is None:
                        bindings = Bindings.from_context(self, context)
                    v = self._derive_from_expr(slot_derivation, bindings)
                elif slot_derivation.populated_from:
                    populated_from = slot_derivation.populated_from

                    if "." in populated_from:
                        table_name, field_path = populated_from.split(".", 1)
                        if class_deriv.joins and table_name in class_deriv.joins:
                            (v, source_class_slot) = self._perform_join_resolution(table_name, field_path, context)
                        else:
                            (v, source_class_slot) = self._resolve_fk_or_literal(
                                populated_from,
                                slot_derivation,
                                sv,
                                source_type,
                                source_obj,
                                require_fk=True,
                            )
                    else:
                        (v, source_class_slot) = self._resolve_fk_or_literal(
                            populated_from,
                            slot_derivation,
                            sv,
                            source_type,
                            source_obj,
                        )

                    if slot_derivation.value_mappings and v is not None:
                        mapped = slot_derivation.value_mappings.get(str(v), None)
                        v = mapped.value if mapped is not None else None

                    if slot_derivation.offset and v is not None:
                        v = self._apply_offset(v, slot_derivation, source_obj)

                    logger.debug(
                        f"Pop slot {slot_derivation.name} => {v} using {slot_derivation.populated_from} // {source_obj}"
                    )
                elif slot_derivation.sources:
                    (v, source_class_slot) = self._resolve_sources(slot_derivation, context)
                elif slot_derivation.object_derivations:
                    v = self._derive_nested_objects(slot_derivation, source_obj, target_type)
                else:
                    source_class_slot = sv.induced_slot(slot_derivation.name, source_type)
                    v = source_obj.get(slot_derivation.name, None)

                if source_class_slot and v is not None:
                    target_range = slot_derivation.range
                    v = self._map_value_by_range(v, source_class_slot, target_range, source_obj)
                    v = self._coerce_cardinality(v, slot_derivation, class_deriv)
                    v = self._coerce_datatype(v, target_range)
                    v = self._reshape_collection(v, slot_derivation, source_class_slot)
            except TransformationError:
                raise
            except Exception as exc:
                raise TransformationError(
                    message=str(exc),
                    class_derivation_name=class_deriv.name,
                    slot_derivation_name=slot_derivation.name,
                    source_row=source_obj,
                    cause=exc,
                ) from exc
            tgt_attrs[str(slot_derivation.name)] = v
        return tgt_attrs

    def _derive_from_expr(self, slot_derivation: SlotDerivation, bindings: Bindings) -> Any:
        """Evaluate a slot derivation expression, with fallback to asteval for unrestricted mode."""
        try:
            return eval_expr_with_mapping(slot_derivation.expr, bindings)
        except Exception as err:
            # Broad catch is intentional: simpleeval raises various exception types
            # (NameNotDefined, FeatureNotAvailable, etc.) for expressions outside its
            # safe subset. Should also handle KeyError, TypeError in the future.
            if not self.unrestricted_eval:
                logger.warning(f"Expression evaluation failed for '{slot_derivation.name}': {err}")
                msg = f"Expression not in safe subset: {slot_derivation.expr}"
                raise RuntimeError(msg) from err
            ctxt_obj, _ = bindings.get_ctxt_obj_and_dict()
            aeval = Interpreter(usersyms={"src": ctxt_obj, "target": None, "uuid5": _uuid5})
            aeval(slot_derivation.expr)
            return aeval.symtable["target"]

    def _perform_fk_resolution(
        self,
        fk_resolution: FKResolution,
        slot_derivation: SlotDerivation,
        fk_value: Any,
    ) -> tuple[Any, Optional[SlotDefinition]]:
        """Resolve a foreign key value through the object index and walk the remaining path."""
        if fk_value is not None and self.object_index:
            cache_key = (fk_resolution.target_class, str(fk_value))
            referenced_obj = self.object_index._source_object_cache.get(cache_key)

            if referenced_obj:
                v = referenced_obj
                for attr in fk_resolution.remaining_path.split("."):
                    if isinstance(v, dict):
                        v = v.get(attr)
                    elif v is not None:
                        v = getattr(v, attr, None)
                    if v is None:
                        break
            else:
                v = None
                logger.debug(f"FK reference not found for {slot_derivation.name}")
        else:
            v = None
            if fk_value is not None and not self.object_index:
                logger.warning(
                    "Cross-class lookup requires object_index. Call transformer.index(container_data) first."
                )

        source_class_slot = fk_resolution.final_slot
        return v, source_class_slot

    def _resolve_fk_or_literal(
        self,
        populated_from: str,
        slot_derivation: SlotDerivation,
        sv: SchemaView,
        source_type: str,
        source_obj: DICT_OBJ,
        *,
        require_fk: bool = False,
    ) -> tuple[Any, Optional[SlotDefinition]]:
        """Resolve a populated_from value via FK path or direct field lookup.

        :param populated_from: The populated_from string (may contain dots for FK paths).
        :param slot_derivation: The active slot derivation.
        :param sv: Source schema view.
        :param source_type: Source class name.
        :param source_obj: Current source row.
        :param require_fk: If True, raise ValueError when no FK path is found
            (used for dot-notation without a matching join).
        :returns: Tuple of (resolved value, source slot definition or None).
        """
        fk_resolution = resolve_fk_path(sv, source_type, populated_from)
        if fk_resolution:
            fk_value = source_obj.get(fk_resolution.fk_slot_name)
            return self._perform_fk_resolution(fk_resolution, slot_derivation, fk_value)
        if require_fk:
            msg = (
                f"Dot-notation '{populated_from}' in populated_from "
                f"requires a matching join spec or FK path, but neither was found"
            )
            raise ValueError(msg)
        v = source_obj.get(populated_from, None)
        source_class_slot = sv.induced_slot(populated_from, source_type)
        return v, source_class_slot

    def _resolve_joined_row(
        self,
        table_name: str,
        source_obj: DICT_OBJ,
        class_deriv: ClassDerivation,
    ) -> dict | None:
        """Resolve a row from a joined table using LookupIndex.

        This is the single source of truth for cross-table join resolution.
        Both ``Bindings._resolve_join`` (for ``expr:``) and
        ``_perform_join_resolution`` (for ``populated_from:``) delegate here.

        :param table_name: Join name (key in ``class_deriv.joins``).
        :param source_obj: Current primary-table row.
        :param class_deriv: The active ClassDerivation (carries join specs).
        :returns: Matched row as a dict, or ``None`` if no match found.
        :raises ValueError: If join spec is missing keys or lookup_index is not initialized.
        """
        spec = class_deriv.joins[table_name]
        source_key = spec.source_key or spec.join_on
        lookup_key = spec.lookup_key or spec.join_on
        if not source_key or not lookup_key:
            msg = f"Join spec for {table_name!r} must specify 'join_on' or both 'source_key' and 'lookup_key'"
            raise ValueError(msg)
        key_val = source_obj.get(source_key)
        if key_val is None:
            return None
        if self.lookup_index is None:
            msg = f"Join configured for {table_name!r} but lookup_index has not been initialized"
            raise ValueError(msg)
        return self.lookup_index.lookup_row(table_name, lookup_key, key_val)

    def _perform_join_resolution(
        self,
        table_name: str,
        field_path: str,
        context: DerivationContext,
    ) -> tuple[Any, Optional[SlotDefinition]]:
        """Resolve a slot value via cross-table join lookup.

        :param table_name: Join name (key in ``class_deriv.joins``).
        :param field_path: Column name within the joined table.
        :param context: Current derivation context.
        :returns: Tuple of (resolved value, source slot definition or None).
        """
        row = self._resolve_joined_row(table_name, context.source_obj, context.class_deriv)
        v = row.get(field_path) if row else None
        joined_class = context.class_deriv.joins[table_name].class_named or table_name
        source_class_slot = None
        if joined_class in context.sv.all_classes():
            if field_path in context.sv.class_induced_slots(joined_class):
                source_class_slot = context.sv.induced_slot(field_path, joined_class)
        return v, source_class_slot

    def _apply_offset(self, value: Any, slot_derivation: SlotDerivation, source_obj: DICT_OBJ) -> Any:
        """Apply an offset calculation using a value from another source field."""
        off = slot_derivation.offset
        off_field_val = source_obj.get(off.offset_field)

        if off_field_val is None:
            logger.debug(
                f"Offset field '{off.offset_field}' not found in source object; "
                f"skipping offset for '{slot_derivation.name}'"
            )
            return value

        delta = off.offset_value * off_field_val
        result = value - delta if off.offset_reverse else value + delta
        logger.debug(
            f"Offset for '{slot_derivation.name}': "
            f"{value} {'-' if off.offset_reverse else '+'} "
            f"({off.offset_value} * {off_field_val}) = {result}"
        )
        return result

    def _resolve_sources(
        self, slot_derivation: SlotDerivation, context: DerivationContext
    ) -> tuple[Any, Optional[SlotDefinition]]:
        """Resolve a slot value from multiple candidate source slots (first available wins)."""
        vmap = {s: context.source_obj.get(s, None) for s in slot_derivation.sources}
        vmap = {k: v for k, v in vmap.items() if v is not None}
        if len(vmap.keys()) > 1:
            msg = f"Multiple sources for {slot_derivation.name}: {vmap}"
            raise ValueError(msg)
        if len(vmap.keys()) == 1:
            v = next(iter(vmap.values()))
            source_class_slot_name = next(iter(vmap.keys()))
            source_class_slot = context.sv.induced_slot(source_class_slot_name, context.source_type)
        else:
            v = None
            source_class_slot = None

        logger.debug(
            f"Pop slot {slot_derivation.name} => {v} using {slot_derivation.populated_from} // {context.source_obj}"
        )
        return v, source_class_slot

    def _derive_nested_objects(self, slot_derivation: SlotDerivation, source_obj: DICT_OBJ, target_type: str) -> Any:
        """Build nested objects from explicit object_derivation declarations."""
        derived_objs = []

        for obj_derivation in slot_derivation.object_derivations:
            for target_cls, cls_derivation in obj_derivation.class_derivations.items():
                # Determine the correct source object to use
                source_sub_obj = source_obj  # You may refine this if needed

                # Recursively map the sub-object
                nested_result = self.map_object(
                    source_sub_obj,
                    source_type=cls_derivation.populated_from,
                    target_type=target_cls,
                    class_derivation=cls_derivation,
                )
                derived_objs.append(nested_result)

        # If the slot is multivalued, we assign the whole list
        # Otherwise, just assign the first (for now; error/warning later if >1)
        target_class_slot = self.target_schemaview.induced_slot(slot_derivation.name, target_type)
        if target_class_slot.multivalued:
            v = derived_objs
        else:
            v = derived_objs[0] if derived_objs else None
        return v

    def _map_value_by_range(
        self,
        v: Any,
        source_class_slot: SlotDefinition,
        target_range: Optional[str],
        source_obj: DICT_OBJ,
    ) -> Any:
        """Recursively map nested values based on the source slot's range type."""
        source_class_slot_range = source_class_slot.range
        sv = self.source_schemaview

        # Check for enums defined via any_of when the range is None or "Any"
        if source_class_slot_range is None or source_class_slot_range == "Any":
            any_of_enums = self._get_any_of_enum_names(source_class_slot, sv)
            if any_of_enums:
                if source_class_slot.multivalued and isinstance(v, list):
                    return [self.transform_enum(v1, any_of_enums, source_obj) for v1 in v]
                return self.transform_enum(v, any_of_enums, source_obj)
            # No range and no any_of enums: nothing to recurse into for scalars
            if not isinstance(v, (dict, list)):
                return v
            if isinstance(v, list) and all(not isinstance(v1, (dict, list)) for v1 in v):
                return v

        if source_class_slot.multivalued:
            if isinstance(v, list):
                return [self.map_object(v1, source_class_slot_range, target_range) for v1 in v]
            elif isinstance(v, dict):
                return {k1: self.map_object(v1, source_class_slot_range, target_range) for k1, v1 in v.items()}
            else:
                return [self.map_object(v, source_class_slot_range, target_range)]
        else:
            return self.map_object(v, source_class_slot_range, target_range)

    def _coerce_cardinality(self, v: Any, slot_derivation: SlotDerivation, class_derivation: ClassDerivation) -> Any:
        """Coerce between single-valued and multi-valued based on target schema and spec."""
        if (
            self._is_coerce_to_multivalued(slot_derivation, class_derivation)
            and v is not None
            and not isinstance(v, list)
        ):
            return self._singlevalued_to_multivalued(v, slot_derivation)
        elif self._is_coerce_to_singlevalued(slot_derivation, class_derivation) and isinstance(v, list):
            return self._multivalued_to_singlevalued(v, slot_derivation)
        return v

    def _reshape_collection(self, v: Any, slot_derivation: SlotDerivation, source_class_slot: SlotDefinition) -> Any:
        """Reshape between list and compact-dict collection formats."""
        if slot_derivation.dictionary_key and isinstance(v, list):
            # List to CompactDict
            v = {v1[slot_derivation.dictionary_key]: v1 for v1 in v}
            for v1 in v.values():
                del v1[slot_derivation.dictionary_key]
            return v
        elif (
            slot_derivation.cast_collection_as
            and slot_derivation.cast_collection_as == CollectionType.MultiValuedList
            and isinstance(v, dict)
        ):
            # CompactDict to List
            src_rng = source_class_slot.range
            src_rng_id_slot = self.source_schemaview.get_identifier_slot(src_rng, use_key=True)
            if src_rng_id_slot:
                return [{**v1, src_rng_id_slot.name: k} for k, v1 in v.items()]
            else:
                return list(v.values())
        return v

    @staticmethod
    def _get_any_of_enum_names(slot: Any, sv: SchemaView) -> list[str]:
        """Extract enum names from a slot's any_of constraints.

        :param slot: An induced slot definition (from SchemaView.induced_slot).
        :param sv: Source schema view.
        :return: List of enum names found in any_of, empty if none.
        """
        if not hasattr(slot, "any_of") or not slot.any_of:
            return []
        all_enums = sv.all_enums()
        return [ao.range for ao in slot.any_of if ao.range in all_enums]

    def _perform_unit_conversion(
        self,
        slot_derivation: SlotDerivation,
        context: DerivationContext,
    ) -> Union[float, dict, None]:
        """Perform unit conversion for a slot derivation."""
        uc = slot_derivation.unit_conversion
        curr_v = context.source_obj.get(slot_derivation.populated_from, None)

        if curr_v is None:
            logger.debug(f"No value found for slot '{slot_derivation.populated_from}'; skipping conversion")
            return None

        slot = context.sv.induced_slot(slot_derivation.populated_from, context.source_type)
        schema_unit = None
        from_unit = None
        system = UnitSystem.UCUM

        if slot.unit:
            if slot.unit.ucum_code:
                schema_unit = slot.unit.ucum_code
            elif slot.unit.iec61360code:
                schema_unit = slot.unit.iec61360code
                system = UnitSystem.IEC61360
            elif slot.unit.symbol:
                schema_unit = slot.unit.symbol
                system = None
            elif slot.unit.abbreviation:
                schema_unit = slot.unit.abbreviation
                system = None
            elif slot.unit.descriptive_name:
                schema_unit = slot.unit.descriptive_name
                system = None
            else:
                raise NotImplementedError(
                    f"Cannot determine unit system for slot '{slot.name}' — all unit fields are None"
                )

        spec_unit = uc.source_unit if uc.source_unit else None

        if schema_unit and spec_unit:
            if schema_unit != spec_unit:
                raise ValueError(
                    f"Mismatch in source units for slot '{slot_derivation.populated_from}': "
                    f"schema unit '{schema_unit}' vs. transformation spec '{spec_unit}'"
                )
            from_unit = schema_unit
        elif schema_unit:
            from_unit = schema_unit
        elif spec_unit:
            from_unit = spec_unit
        else:
            if uc.source_unit_slot:
                from_unit = None
            else:
                slot_name = slot_derivation.populated_from
                raise ValueError(f"No source unit provided in schema or transformation spec for slot '{slot_name}'")

        if uc.source_unit_slot:
            # Structured input, e.g., {"value": 120, "unit": "cm"}
            from_unit_val = curr_v.get(uc.source_unit_slot)
            if from_unit_val:
                if from_unit and from_unit_val != from_unit:
                    slot_name = slot_derivation.populated_from
                    raise ValueError(
                        f"Value unit '{from_unit_val}' does not match expected '{from_unit}' for slot '{slot_name}'"
                    )
                from_unit = from_unit_val
            else:
                raise ValueError(
                    f"Missing unit in structured value for slot '{slot_derivation.populated_from}': {curr_v}"
                )

            magnitude = curr_v.get(uc.source_magnitude_slot)
            if magnitude is None:
                raise ValueError(
                    f"Missing magnitude in structured value for slot '{slot_derivation.populated_from}': {curr_v}"
                )
        else:
            magnitude = curr_v

        if uc.none_if_non_numeric:
            try:
                float(magnitude)
            except (TypeError, ValueError):
                return None

        to_unit = uc.target_unit or from_unit
        if from_unit == to_unit:
            result = magnitude
        else:
            result = convert_units(magnitude, from_unit=from_unit, to_unit=to_unit, system=system)

        if uc.target_magnitude_slot:
            return {uc.target_magnitude_slot: result, uc.target_unit_slot: to_unit}
        return result

    def _multivalued_to_singlevalued(self, vs: list[Any], slot_derivation: SlotDerivation) -> Any:
        if slot_derivation.stringification:
            stringification = slot_derivation.stringification
            delimiter = stringification.delimiter
            if delimiter:
                return delimiter.join(vs)
            if stringification.syntax:
                if stringification.syntax == SerializationSyntaxType.JSON:
                    return json.dumps(vs)
                if stringification.syntax == SerializationSyntaxType.YAML:
                    return yaml.dump(vs, default_flow_style=True).strip()
                msg = f"Unknown syntax: {stringification.syntax}"
                raise ValueError(msg)
            msg = f"Cannot convert multivalued to single valued: {vs}; no delimiter"
            raise ValueError(msg)
        if len(vs) > 1:
            msg = f"Cannot coerce multiple values {vs}"
            raise ValueError(msg)
        if len(vs) == 0:
            return None
        return vs[0]

    def _singlevalued_to_multivalued(self, v: Any, slot_derivation: SlotDerivation) -> list[Any]:
        stringification = slot_derivation.stringification
        if stringification:
            delimiter = stringification.delimiter
            if delimiter:
                vs = v.split(slot_derivation.stringification.delimiter)
                if vs == [""]:
                    vs = []
            elif stringification.syntax:
                syntax = stringification.syntax
                if syntax == SerializationSyntaxType.JSON:
                    vs = json.loads(v)
                elif syntax == SerializationSyntaxType.YAML:
                    vs = yaml.safe_load(v)
                else:
                    msg = f"Unknown syntax: {syntax}"
                    raise ValueError(msg)
            else:
                msg = f"Cannot convert single valued to multivalued: {v}; no delimiter"
                raise ValueError(msg)
            return vs
        return [v]

    def transform_object(
        self,
        source_obj: Union[YAMLRoot, BaseModel],
        target_class: Optional[Union[type[YAMLRoot], type[BaseModel]]] = None,
    ) -> Union[YAMLRoot, BaseModel]:
        """
        Transform an object into an object of class target_class.

        :param source_obj: source object
        :type source_obj: Union[YAMLRoot, BaseModel]
        :param target_class: class to transform the object into, defaults to None
        :type target_class: Optional[Union[Type[YAMLRoot], Type[BaseModel]]], optional
        :return: transformed object of class target_class
        :rtype: Union[YAMLRoot, BaseModel]
        """
        if not target_class:
            msg = "No target_class specified for transform_object"
            raise ValueError(msg)

        source_type = type(source_obj)
        source_type_name = source_type.__name__
        # if isinstance(source_obj, YAMLRoot):
        #    source_obj_dict = json_dumper.to_dict(source_obj)
        # elif isinstance(source_obj, BaseModel):
        #    source_obj_dict = source_obj.dict()
        # else:
        #    raise ValueError(f"Do not know how to handle type: {typ}")
        tr_obj_dict = self.map_object(source_obj, source_type_name)
        return target_class(**tr_obj_dict)

    def transform_enum(self, source_value: str, enum_names: list[str], source_obj: Any) -> Optional[str]:
        """Transform a source enum value through one or more enum derivations.

        Iterates *enum_names* in order. For each enum derivation, tries
        expression evaluation first, then permissible-value mappings.
        If mirror_source is set on a derivation and no mapping matched,
        returns the source value unchanged without trying further enums.

        :param source_value: The source enum value to transform.
        :param enum_names: Ordered list of source enum names to try.
        :param source_obj: The full source object (used for expr evaluation).
        :return: Transformed value, or None if no mapping found.
        """
        for enum_name in enum_names:
            enum_deriv = self._get_enum_derivation(enum_name)
            if enum_deriv.expr:
                try:
                    v = eval_expr(enum_deriv.expr, **source_obj, NULL=None)
                except Exception:
                    aeval = Interpreter(usersyms={"src": source_obj, "target": None, "uuid5": _uuid5})
                    aeval(enum_deriv.expr)
                    v = aeval.symtable["target"]
                if v is not None:
                    return v
            for pv_deriv in enum_deriv.permissible_value_derivations.values():
                if source_value == pv_deriv.populated_from:
                    return pv_deriv.name
                if source_value in pv_deriv.sources:
                    return pv_deriv.name
            if enum_deriv.mirror_source:
                return str(source_value)
        return None

    def _perform_pivot_operation(
        self,
        pivot_op: PivotOperation,
        source_obj: DICT_OBJ,
        class_deriv: ClassDerivation,
        sv: SchemaView,
        source_type: str,
    ) -> Union[DICT_OBJ, list[DICT_OBJ]]:
        """
        Perform a pivot (MELT or UNMELT) operation.

        :param pivot_op: The pivot operation configuration
        :param source_obj: The source object to transform
        :param class_deriv: The class derivation spec
        :param sv: Source schema view
        :param source_type: Source type name
        :return: Transformed object(s)
        """
        if pivot_op.direction == PivotDirectionType.UNMELT:
            return self._perform_unmelt(pivot_op, source_obj, class_deriv, sv, source_type)
        elif pivot_op.direction == PivotDirectionType.MELT:
            return self._perform_melt(pivot_op, source_obj, class_deriv)
        else:
            msg = f"Unknown pivot direction: {pivot_op.direction}"
            raise ValueError(msg)

    def _perform_unmelt(
        self,
        pivot_op: PivotOperation,
        source_obj: DICT_OBJ,
        class_deriv: ClassDerivation,
        sv: SchemaView,
        source_type: str,
    ) -> DICT_OBJ:
        """
        Transform EAV/long format to wide format.

        Handles both single record and collection-based unmelt:
        - Single record: {att: 'len', val: 1.0} -> {len: 1.0}
        - Collection: [{att: 'h', val: 1.8}, {att: 'w', val: 75}] -> {h: 1.8, w: 75}

        :param pivot_op: The pivot operation configuration
        :param source_obj: The source object (may contain EAV records)
        :param class_deriv: The class derivation spec
        :param sv: Source schema view
        :param source_type: Source type name
        :return: Wide-format object
        """
        variable_slot = pivot_op.variable_slot or "variable"
        value_slot = pivot_op.value_slot or "value"
        unit_slot = pivot_op.unit_slot
        template = pivot_op.slot_name_template or "{variable}"

        # Check if source_obj itself is an EAV record (has variable and value slots)
        if variable_slot in source_obj and value_slot in source_obj:
            return self._unmelt_single_record(pivot_op, source_obj, variable_slot, value_slot, unit_slot, template)

        # Otherwise, look for a collection of EAV records in the source
        # Try to find a multivalued slot containing EAV records
        for slot_name, slot_value in source_obj.items():
            if isinstance(slot_value, list) and len(slot_value) > 0:
                first_item = slot_value[0]
                if isinstance(first_item, dict) and variable_slot in first_item:
                    return self._unmelt_collection(pivot_op, slot_value)

        # Fallback: treat source_obj as a single EAV record
        return self._unmelt_single_record(pivot_op, source_obj, variable_slot, value_slot, unit_slot, template)

    def _unmelt_single_record(
        self,
        pivot_op: PivotOperation,
        record: DICT_OBJ,
        variable_slot: str,
        value_slot: str,
        unit_slot: Optional[str],
        template: str,
    ) -> DICT_OBJ:
        """
        Unmelt a single EAV record into slot assignment(s).

        Example:
            Input:  {att: 'len', val: 1.0, unit: 'm'}
            Output: {len_m: 1.0}
        """
        result = {}

        # Copy ID slots (non-pivoted attributes)
        if pivot_op.id_slots:
            for id_slot in pivot_op.id_slots:
                if id_slot in record:
                    result[id_slot] = record[id_slot]

        # Get variable and value
        variable = record.get(variable_slot)
        value = record.get(value_slot)

        if variable is None:
            logger.warning(f"No variable found in slot '{variable_slot}'")
            return result

        # Generate target slot name
        if unit_slot and unit_slot in record:
            unit = record[unit_slot]
            target_slot_name = template.format(variable=variable, unit=unit)
        else:
            target_slot_name = template.format(variable=variable, unit="")

        # Validate against target schema if unmelt_to_class specified
        if pivot_op.unmelt_to_class and self.target_schemaview:
            valid_slots = [s.name for s in self.target_schemaview.class_induced_slots(pivot_op.unmelt_to_class)]
            if pivot_op.unmelt_to_slots:
                valid_slots = [s for s in valid_slots if s in pivot_op.unmelt_to_slots]

            if target_slot_name not in valid_slots:
                logger.warning(
                    f"Generated slot name '{target_slot_name}' not in valid slots for "
                    f"class '{pivot_op.unmelt_to_class}'"
                )

        result[target_slot_name] = value
        return result

    def _unmelt_collection(
        self,
        pivot_op: PivotOperation,
        records: list[DICT_OBJ],
    ) -> DICT_OBJ:
        """
        Unmelt a collection of EAV records into a single wide object.

        Example:
            Input:  [{att: 'height', val: 1.8}, {att: 'weight', val: 75.0}]
            Output: {height: 1.8, weight: 75.0}
        """
        result = {}
        variable_slot = pivot_op.variable_slot or "variable"
        value_slot = pivot_op.value_slot or "value"
        unit_slot = pivot_op.unit_slot
        template = pivot_op.slot_name_template or "{variable}"

        for record in records:
            variable = record.get(variable_slot)
            value = record.get(value_slot)

            if variable is None:
                continue

            if unit_slot and unit_slot in record:
                unit = record[unit_slot]
                target_slot = template.format(variable=variable, unit=unit)
            else:
                target_slot = template.format(variable=variable, unit="")

            if target_slot in result:
                logger.warning(f"Duplicate variable '{variable}' in unmelt; last value wins")

            result[target_slot] = value

        # Copy ID slots from the first record (assuming they're the same across all)
        if pivot_op.id_slots and records:
            for id_slot in pivot_op.id_slots:
                if id_slot in records[0]:
                    result[id_slot] = records[0][id_slot]

        return result

    def _perform_melt(
        self,
        pivot_op: PivotOperation,
        source_obj: DICT_OBJ,
        slot_derivation: Optional[SlotDerivation] = None,
    ) -> list[DICT_OBJ]:
        """
        Transform wide format to EAV/long format.

        Example:
            Input:  {height: 1.8, weight: 75.0}
            Output: [{variable: 'height', value: 1.8}, {variable: 'weight', value: 75.0}]

        :param pivot_op: The pivot operation configuration
        :param source_obj: The source object in wide format
        :param slot_derivation: Optional slot derivation (for context)
        :return: List of EAV records
        """
        variable_slot = pivot_op.variable_slot or "variable"
        value_slot = pivot_op.value_slot or "value"

        # Determine which slots to melt
        if pivot_op.source_slots:
            slots_to_melt = list(pivot_op.source_slots)
        elif pivot_op.unmelt_to_class and self.target_schemaview:
            # Infer from target class
            slots_to_melt = [s.name for s in self.target_schemaview.class_induced_slots(pivot_op.unmelt_to_class)]
        else:
            # Melt all non-ID slots
            id_slots = set(pivot_op.id_slots or [])
            slots_to_melt = [k for k in source_obj.keys() if k not in id_slots]

        results = []
        base_record = {}

        # Copy ID slots to base record
        if pivot_op.id_slots:
            for id_slot in pivot_op.id_slots:
                if id_slot in source_obj:
                    base_record[id_slot] = source_obj[id_slot]

        # Create one record per melted slot
        for slot_name in slots_to_melt:
            if slot_name in source_obj and source_obj[slot_name] is not None:
                record = base_record.copy()
                record[variable_slot] = slot_name
                record[value_slot] = source_obj[slot_name]
                results.append(record)

        return results
