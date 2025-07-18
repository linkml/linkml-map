"""A Transformer that works on in-memory dict objects."""

import json
import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Optional, Union

import yaml
from asteval import Interpreter
from linkml_runtime import SchemaView
from linkml_runtime.index.object_index import ObjectIndex
from linkml_runtime.utils.yamlutils import YAMLRoot
from pydantic import BaseModel

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    SerializationSyntaxType,
    SlotDerivation,
)
from linkml_map.functions.unit_conversion import UnitSystem, convert_units
from linkml_map.transformer.transformer import OBJECT_TYPE, Transformer
from linkml_map.utils.dynamic_object import DynObj, dynamic_object
from linkml_map.utils.eval_utils import eval_expr, eval_expr_with_mapping

DICT_OBJ = dict[str, Any]


logger = logging.getLogger(__name__)


class Bindings(Mapping):
    """
    Efficiently access source object attributes.
    """

    def __init__(  # noqa: PLR0913
        self,
        object_transformer: "ObjectTransformer",
        source_obj: OBJECT_TYPE,
        source_obj_typed: OBJECT_TYPE,
        source_type: str,
        sv: SchemaView,
        bindings: dict,
    ) -> None:
        self.object_transformer: ObjectTransformer = object_transformer
        self.source_obj: OBJECT_TYPE = source_obj
        self.source_obj_typed: OBJECT_TYPE = source_obj_typed
        self.source_type: str = source_type
        self.sv: SchemaView = sv
        self.bindings: dict = {}
        if bindings:
            self.bindings.update(bindings)

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
            ctxt_dict = {
                k: getattr(ctxt_obj, k) for k in ctxt_obj._attributes() if not k.startswith("_")
            }
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

    def __getitem__(self, name: Any) -> Any:
        if name not in self.bindings:
            _ = self.get_ctxt_obj_and_dict({name: self.source_obj[name]})

        return self.bindings.get(name)

    def __setitem__(self, name: Any, value: Any) -> None:
        del name, value
        msg = f"__setitem__ not allowed on class {self.__class__.__name__}"
        raise RuntimeError(msg)


@dataclass
class ObjectTransformer(Transformer):
    """
    A Transformer that works on in-memory dict objects.

    This works recursively
    """

    object_index: ObjectIndex = None

    def index(self, source_obj: Any, target: Optional[str] = None) -> None:
        """
        Create an index over a container object.

        :param source_obj: source data structure to be indexed
        :param target: class to convert source object into
        """
        if isinstance(source_obj, dict):
            if target is None:
                [target] = [
                    c.name for c in self.source_schemaview.all_classes().values() if c.tree_root
                ]
            if target is None:
                msg = f"target must be passed if source_obj is dict: {source_obj}"
                raise ValueError(msg)
            source_obj_typed = dynamic_object(source_obj, self.source_schemaview, target)
            self.object_index = ObjectIndex(source_obj_typed, schemaview=self.source_schemaview)
        else:
            self.object_index = ObjectIndex(source_obj, schemaview=self.source_schemaview)

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
        if source_type is None and sv is None:
            # TODO: use smarter method
            source_type = next(iter(self.specification.class_derivations.values())).name
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
            # TODO: enum derivations
            return self.transform_enum(source_obj, source_type, source_obj)
        source_obj_typed = None
        if isinstance(source_obj, (BaseModel, YAMLRoot)):
            # ensure dict
            source_obj_typed = source_obj
            source_obj = vars(source_obj)
        if not isinstance(source_obj, dict):
            logger.warning(f"Unexpected: {source_obj} for type {source_type}")
            return source_obj
        class_deriv = class_derivation or self._get_class_derivation(source_type)
        tgt_attrs = {}
        bindings = None
        # map each slot assignment in source_obj, if there is a slot_derivation
        for slot_derivation in class_deriv.slot_derivations.values():
            v = None
            source_class_slot = None
            if slot_derivation.value is not None:
                v = slot_derivation.value
                if slot_derivation.range is None:
                    slot_derivation.range = "string"
            elif slot_derivation.unit_conversion:
                v = self._perform_unit_conversion(slot_derivation, source_obj, sv, source_type)
            elif slot_derivation.expr:
                if bindings is None:
                    bindings = Bindings(
                        self,
                        source_obj=source_obj,
                        source_obj_typed=source_obj_typed,
                        source_type=source_type,
                        sv=sv,
                        bindings={"NULL": None},
                    )

                try:
                    v = eval_expr_with_mapping(slot_derivation.expr, bindings)
                except Exception as err:
                    if not self.unrestricted_eval:
                        msg = f"Expression not in safe subset: {slot_derivation.expr}"
                        raise RuntimeError(msg) from err
                    ctxt_obj, _ = bindings.get_ctxt_obj_and_dict()
                    aeval = Interpreter(usersyms={"src": ctxt_obj, "target": None})
                    aeval(slot_derivation.expr)
                    v = aeval.symtable["target"]
            elif slot_derivation.populated_from:
                v = source_obj.get(slot_derivation.populated_from, None)
                if slot_derivation.value_mappings and v is not None:
                    mapped = slot_derivation.value_mappings.get(str(v), None)
                    v = mapped.value if mapped is not None else None
                source_class_slot = sv.induced_slot(slot_derivation.populated_from, source_type)
                logger.debug(
                    f"Pop slot {slot_derivation.name} => {v} using {slot_derivation.populated_from} // {source_obj}"
                )
            elif slot_derivation.sources:
                vmap = {s: source_obj.get(s, None) for s in slot_derivation.sources}
                vmap = {k: v for k, v in vmap.items() if v is not None}
                if len(vmap.keys()) > 1:
                    msg = f"Multiple sources for {slot_derivation.name}: {vmap}"
                    raise ValueError(msg)
                if len(vmap.keys()) == 1:
                    v = next(iter(vmap.values()))
                    source_class_slot_name = next(iter(vmap.keys()))
                    source_class_slot = sv.induced_slot(source_class_slot_name, source_type)
                else:
                    v = None
                    source_class_slot = None

                logger.debug(
                    f"Pop slot {slot_derivation.name} => {v} using {slot_derivation.populated_from} // {source_obj}"
                )
            elif slot_derivation.object_derivations:
                # We'll collect all derived objects here
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
            else:
                source_class_slot = sv.induced_slot(slot_derivation.name, source_type)
                v = source_obj.get(slot_derivation.name, None)
            if source_class_slot and v is not None:
                # slot is mapped and there is a value in the assignment
                target_range = slot_derivation.range
                source_class_slot_range = source_class_slot.range
                if source_class_slot.multivalued:
                    if isinstance(v, list):
                        v = [self.map_object(v1, source_class_slot_range, target_range) for v1 in v]
                    elif isinstance(v, dict):
                        v = {
                            k1: self.map_object(v1, source_class_slot_range, target_range)
                            for k1, v1 in v.items()
                        }
                    else:
                        v = [self.map_object(v, source_class_slot_range, target_range)]
                else:
                    v = self.map_object(v, source_class_slot_range, target_range)
                if (
                    self._is_coerce_to_multivalued(slot_derivation, class_deriv)
                    and v is not None
                    and not isinstance(v, list)
                ):
                    v = self._singlevalued_to_multivalued(v, slot_derivation)
                if self._is_coerce_to_singlevalued(slot_derivation, class_deriv) and isinstance(
                    v, list
                ):
                    v = self._multivalued_to_singlevalued(v, slot_derivation)
                v = self._coerce_datatype(v, target_range)
                if slot_derivation.dictionary_key and isinstance(v, list):
                    # List to CompactDict
                    v = {v1[slot_derivation.dictionary_key]: v1 for v1 in v}
                    for v1 in v.values():
                        del v1[slot_derivation.dictionary_key]
                elif (
                    slot_derivation.cast_collection_as
                    and slot_derivation.cast_collection_as == CollectionType.MultiValuedList
                    and isinstance(v, dict)
                ):
                    # CompactDict to List
                    src_rng = source_class_slot.range
                    src_rng_id_slot = self.source_schemaview.get_identifier_slot(
                        src_rng, use_key=True
                    )
                    if src_rng_id_slot:
                        v = [{**v1, src_rng_id_slot.name: k} for k, v1 in v.items()]
                    else:
                        v = list(v.values())
            tgt_attrs[str(slot_derivation.name)] = v
        return tgt_attrs

    def _perform_unit_conversion(
            self,
            slot_derivation: SlotDerivation,
            source_obj: Any,
            sv: SchemaView,
            source_type: str,
    ) -> Union[float, dict, None]:
        uc = slot_derivation.unit_conversion
        curr_v = source_obj.get(slot_derivation.populated_from, None)
        if curr_v is None:
            logger.debug(f"No value found for slot '{slot_derivation.populated_from}'; skipping conversion")
            return None

        # Get the slot from schema
        slot = sv.induced_slot(slot_derivation.populated_from, source_type)
        schema_unit = None
        from_unit = None
        system = UnitSystem.UCUM

        # --- Step 1: Get unit from schema ---
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
                    f"Cannot determine unit system for slot '{slot.name}' — all unit fields are None")

        # --- Step 2: Get unit from transformer spec ---
        spec_unit = uc.source_unit if uc.source_unit else None

        # --- Step 3: Validate unit source ---
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
            # Handle structured unit slot case: don't raise here if source_unit_slot is set,
            # defer unit extraction to Step 4
            if uc.source_unit_slot:
                from_unit = None
            else:
                raise ValueError(
                    f"No source unit provided in schema or transformation spec for slot '{slot_derivation.populated_from}'"
                )

        # --- Step 4: Determine magnitude and possibly from_unit ---
        if uc.source_unit_slot:
            # Structured input, e.g., {"value": 120, "unit": "cm"}
            from_unit_val = curr_v.get(uc.source_unit_slot)
            if from_unit_val:
                if from_unit and from_unit_val != from_unit:
                    raise ValueError(
                        f"Value unit '{from_unit_val}' does not match expected '{from_unit}' for slot '{slot_derivation.populated_from}'"
                    )
                from_unit = from_unit_val
            else:
                raise ValueError(
                    f"Missing unit in structured value for slot '{slot_derivation.populated_from}': {curr_v}")

            magnitude = curr_v.get(uc.source_magnitude_slot)
            if magnitude is None:
                raise ValueError(
                    f"Missing magnitude in structured value for slot '{slot_derivation.populated_from}': {curr_v}")
        else:
            magnitude = curr_v

        # --- Step 5: Convert ---
        to_unit = uc.target_unit or from_unit
        if from_unit == to_unit:
            result = magnitude
        else:
            result = convert_units(magnitude, from_unit=from_unit, to_unit=to_unit, system=system)

        # --- Step 6: Structure result if needed ---
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

    def transform_enum(self, source_value: str, enum_name: str, source_obj: Any) -> Optional[str]:
        enum_deriv = self._get_enum_derivation(enum_name)
        if enum_deriv.expr:
            try:
                if enum_deriv.expr:
                    v = eval_expr(enum_deriv.expr, **source_obj, NULL=None)
            except Exception:
                aeval = Interpreter(usersyms={"src": source_obj, "target": None})
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
