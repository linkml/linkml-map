"""
A SchemaMapper translates a source schema and transformation specification into a target schema.

AKA profiling
"""

import logging
from collections import defaultdict
from copy import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import json_dumper
from linkml_runtime.linkml_model import (
    ClassDefinition,
    ClassDefinitionName,
    Element,
    EnumDefinition,
    PermissibleValue,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.linkml_model.units import UnitOfMeasure

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    CollectionType,
    CopyDirective,
    EnumDerivation,
    TransformationSpecification,
)
from linkml_map.transformer.transformer import Transformer

logger = logging.getLogger(__name__)


@dataclass
class SchemaMapper:
    """
    Translates a source schema and transformation specification into a target schema.
    """

    source_schemaview: SchemaView = None

    transformer: Transformer = None

    source_to_target_class_mappings: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    slot_info: Dict[Tuple[str, str], Any] = field(default_factory=lambda: {})

    def derive_schema(
        self,
        specification: Optional[TransformationSpecification] = None,
        target_schema_id: Optional[str] = None,
        target_schema_name: Optional[str] = None,
        suffix="-derived",
    ) -> SchemaDefinition:
        """
        Use a transformation specification to generate a target/profile schema from a source schema.

        :param specification:
        :return:
        """
        if specification is None:
            specification = self.transformer.specification
        source_schemaview = self.source_schemaview
        source_schema = source_schemaview.schema
        if target_schema_id is None:
            target_schema_id = source_schema.id + suffix
        if target_schema_name is None:
            target_schema_name = source_schema.name + suffix
        target_schema = SchemaDefinition(id=target_schema_id, name=target_schema_name)
        for im in source_schema.imports:
            target_schema.imports.append(im)
        for prefix in source_schema.prefixes.values():
            target_schema.prefixes[prefix.prefix_prefix] = prefix
        for class_derivation in specification.class_derivations.values():
            class_definition = self._derive_class(class_derivation)
            target_schema.classes[class_definition.name] = class_definition
        for enum_derivation in specification.enum_derivations.values():
            enum_definition = self._derive_enum(enum_derivation)
            target_schema.enums[enum_definition.name] = enum_definition
        target_schema.default_range = source_schema.default_range
        for cd in target_schema.classes.values():
            self._rewire_class(cd)
        for (cn, sn), info in self.slot_info.items():
            cd = target_schema.classes[cn]
            sd = cd.attributes[sn]
            for k, v in info.items():
                setattr(sd, k, v)
        return target_schema

    def _derive_class(self, class_derivation: ClassDerivation) -> ClassDefinition:
        """
        Derive a class from a class derivation.
        """
        populated_from = class_derivation.populated_from
        if not populated_from:
            populated_from = class_derivation.name
        logger.info(f"Populating {class_derivation.name} from {populated_from}")
        source_class = self.source_schemaview.get_class(populated_from)
        if source_class is None:
            logger.warning(f"No such class {populated_from}")
            target_class = ClassDefinition(name=class_derivation.name)
        else:
            target_class = copy(source_class)
            target_class.from_schema = None
            target_class.name = class_derivation.name
            target_class.slots = []
            target_class.attributes = {}
            target_class.slot_usage = {}
        for slot_derivation in class_derivation.slot_derivations.values():
            slot_definition = self._derive_slot(slot_derivation)
            target_class.attributes[slot_definition.name] = slot_definition
        self.source_to_target_class_mappings[populated_from].append(target_class.name)
        if class_derivation.overrides:
            curr = json_dumper.to_dict(target_class)
            for k, v in class_derivation.overrides.items():
                curr[k] = v
            target_class = ClassDefinition(**curr)
        return target_class

    def _derive_enum(self, enum_derivation: EnumDerivation) -> EnumDefinition:
        """
        Derive an enum from an enum derivation.

        :param enum_derivation:
        :return:
        """
        populated_from = enum_derivation.populated_from
        if not populated_from:
            populated_from = enum_derivation.name
        source_enum = self.source_schemaview.get_enum(populated_from)
        if source_enum is None:
            logger.warning(f"No such enum {populated_from}")
            target_enum = ClassDefinition(name=enum_derivation.name)
        else:
            target_enum = copy(source_enum)
            target_enum.from_schema = None
            target_enum.name = enum_derivation.name
            target_enum.slots = []
            target_enum.attributes = {}
            target_enum.slot_usage = {}
        for pv_derivation in enum_derivation.permissible_value_derivations.values():
            if pv_derivation.populated_from:
                pv = PermissibleValue(text=pv_derivation.populated_from)
                target_enum.permissible_values[pv.text] = pv
            elif pv_derivation.sources:
                for source in pv_derivation.sources:
                    pv = PermissibleValue(text=source)
                    target_enum.permissible_values[pv.text] = pv
            else:
                raise ValueError(f"Missing populated_from or sources for {pv_derivation}")
        if enum_derivation.mirror_source:
            for pv in source_enum.permissible_values.values():
                if pv.text not in target_enum.permissible_values:
                    target_enum.permissible_values[pv.text] = copy(pv)
        self.source_to_target_class_mappings[populated_from].append(target_enum.name)
        return target_enum

    def _derive_slot(self, slot_derivation) -> SlotDefinition:
        """
        Derive a slot from a slot derivation.
        """
        populated_from = slot_derivation.populated_from
        if not populated_from:
            populated_from = slot_derivation.name
        source_slot = self.source_schemaview.get_slot(populated_from)
        if source_slot is None:
            target_slot = SlotDefinition(name=slot_derivation.name)
        else:
            target_slot = copy(source_slot)
            target_slot.from_schema = None
            target_slot.owner = None
            target_slot.name = slot_derivation.name
        if slot_derivation.range:
            target_slot.range = slot_derivation.range
        if slot_derivation.unit_conversion:
            target_slot.unit = UnitOfMeasure(ucum_code=slot_derivation.unit_conversion.target_unit)
        if slot_derivation.stringification:
            if slot_derivation.stringification.reversed:
                target_slot.multivalued = True
            else:
                target_slot.multivalued = False
        if slot_derivation.dictionary_key:
            target_slot.inlined = True
            target_slot.inlined_as_list = False
            self.slot_info[(target_slot.range, slot_derivation.dictionary_key)] = {
                "identifier": True
            }
        if slot_derivation.cast_collection_as:
            if slot_derivation.cast_collection_as == CollectionType.MultiValued:
                target_slot.inlined = True
            elif slot_derivation.cast_collection_as == CollectionType.MultiValuedList:
                target_slot.inlined_as_list = True
            elif slot_derivation.cast_collection_as == CollectionType.MultiValuedDict:
                target_slot.inlined = True
                target_slot.inlined_as_list = False
        return target_slot

    def _rewire_class(self, class_definition: ClassDefinition):
        if class_definition.is_a:
            class_definition.is_a = self._rewire_parent(class_definition, class_definition.is_a)
        mixins = [self._rewire_parent(class_definition, m) for m in class_definition.mixins]
        class_definition.mixins = [m for m in mixins if m is not None]

    def _rewire_parent(
        self, class_definition: ClassDefinition, parent: ClassDefinitionName
    ) -> Optional[str]:
        if parent in self.source_to_target_class_mappings:
            new_parents = self.source_to_target_class_mappings[parent]
            if len(new_parents) > 1:
                raise ValueError(
                    f"Cannot rewire to non-isomorphic mappings {parent} => {new_parents}"
                )
            if len(new_parents) == 1:
                return new_parents[0]
        parent_cls = self.source_schemaview.get_class(parent)
        if parent_cls.is_a:
            return self._rewire_parent(class_definition, parent_cls.is_a)
        return None

    def copy_attributes(
        self,
        target_element: Element,
        source_element: Element,
        copy_directive: CopyDirective,
    ) -> None:
        """
        Copy attributes from source to target according to a directive.

        :param target_element:
        :param source_element:
        :param copy_directive:
        :return:
        """
        for k, v in vars(source_element).items():
            included = False
            if copy_directive.include_all:
                included = True
            if k in copy_directive.include:
                included = True
            if k in copy_directive.exclude:
                included = False
            if included:
                setattr(target_element, k, v)
