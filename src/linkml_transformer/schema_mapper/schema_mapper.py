from copy import copy
from dataclasses import dataclass

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import (ClassDefinition, Element,
                                         SchemaDefinition, SlotDefinition)

from linkml_transformer.datamodel.transformer_model import (
    ClassDerivation, CopyDirective, TransformationSpecification)


@dataclass
class SchemaMapper:
    """
    Translates a source schema and transformation specification into a target schema.
    """

    source_schemaview: SchemaView = None

    def derive_schema(
        self, specification: TransformationSpecification
    ) -> SchemaDefinition:
        """
        Compile a transformation specification into a schema.

        :param specification:
        :return:
        """
        source_schemaview = self.source_schemaview
        source_schema = source_schemaview.schema
        target_schema = SchemaDefinition(id=source_schema.id, name=source_schema.name)
        for class_derivation in specification.class_derivations.values():
            class_definition = self._derive_class(class_derivation)
            target_schema.classes[class_definition.name] = class_definition
        return target_schema

    def _derive_class(self, class_derivation: ClassDerivation) -> ClassDefinition:
        """
        Derive a class from a class derivation.
        """
        populated_from = class_derivation.populated_from
        if not populated_from:
            populated_from = class_derivation.name
        source_class = self.source_schemaview.get_class(populated_from)
        if source_class is None:
            target_class = ClassDefinition(name=class_derivation.name)
        else:
            target_class = copy(source_class)
            target_class.name = class_derivation.name
            target_class.slots = []
            target_class.attributes = {}
            target_class.slot_usage = {}
        for slot_derivation in class_derivation.slot_derivations.values():
            slot_definition = self._derive_slot(slot_derivation)
            target_class.attributes[slot_definition.name] = slot_definition
        return target_class

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
            target_slot.name = slot_derivation.name
        return target_slot

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
