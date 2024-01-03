import re
from copy import copy
from dataclasses import dataclass, field
from typing import Optional

from linkml_runtime import SchemaView

from linkml_transformer.datamodel.transformer_model import (
    ClassDerivation,
    EnumDerivation,
    PermissibleValueDerivation,
    SlotDerivation,
    TransformationSpecification,
    UnitConversionConfiguration,
)


class NonInvertibleSpecification(ValueError):
    pass


@dataclass
class TransformationSpecificationInverter:
    """
    Invert a transformation specification.
    """

    source_schemaview: SchemaView = None
    target_schemaview: SchemaView = None
    strict: bool = field(default=True)

    def invert(self, spec: TransformationSpecification):
        """
        Invert a transformation specification.

        :param spec:
        :return:
        """
        inverted_spec = TransformationSpecification()
        for cd in spec.class_derivations.values():
            inverted_cd = self.invert_class_derivation(cd, spec)
            inverted_spec.class_derivations[inverted_cd.name] = inverted_cd
        for ed in spec.enum_derivations.values():
            inverted_ed = self.invert_enum_derivation(ed, spec)
            inverted_spec.enum_derivations[inverted_ed.name] = inverted_ed
        return inverted_spec

    def invert_class_derivation(self, cd: ClassDerivation, spec: TransformationSpecification):
        """
        Invert a class derivation.

        :param cd:
        :param spec:
        :return:
        """
        inverted_cd = ClassDerivation(
            name=cd.populated_from if cd.populated_from else cd.name, populated_from=cd.name
        )
        for sd in cd.slot_derivations.values():
            inverted_sd = self.invert_slot_derivation(sd, cd, spec)
            if inverted_sd:
                inverted_cd.slot_derivations[inverted_sd.name] = inverted_sd
            else:
                if self.strict:
                    raise NonInvertibleSpecification(f"Cannot invert slot derivation: {sd.name}")
        return inverted_cd

    def invert_enum_derivation(self, ed: EnumDerivation, spec: TransformationSpecification):
        """
        Invert an enum derivation.

        :param ed:
        :param spec:
        :return:
        """
        inverted_ed = EnumDerivation(
            name=ed.populated_from if ed.populated_from else ed.name, populated_from=ed.name
        )
        if inverted_ed.expr:
            raise NonInvertibleSpecification("TODO: invert enum derivation with expression")
        for pv_deriv in ed.permissible_value_derivations.values():
            inverted_pv_deriv = PermissibleValueDerivation(
                name=pv_deriv.populated_from if pv_deriv.populated_from else pv_deriv.name,
                populated_from=pv_deriv.name,
            )
            inverted_ed.permissible_value_derivations[inverted_pv_deriv.name] = inverted_pv_deriv
        return inverted_ed

    def invert_slot_derivation(
        self, sd: SlotDerivation, cd: ClassDerivation, spec: TransformationSpecification
    ) -> Optional[SlotDerivation]:
        """
        Invert a slot derivation.

        :param sd:
        :param cd:
        :param spec:
        :return:
        """
        populated_from = sd.populated_from
        if sd.expr:
            if re.match(r"^\w+$", sd.expr):
                populated_from = sd.expr
            else:
                if not self.strict:
                    return None
                # TODO: add logic for reversible expressions
                raise NonInvertibleSpecification(
                    f"Cannot invert expression {sd.expr} in slot derivation: {sd.name}"
                )
        if not populated_from:
            # use defaults. TODO: decide on semantics of defaults
            populated_from = sd.name
            # raise NonInvertibleSpecification(f"No populate_from or expr in slot derivation: {sd.name}")
        inverted_sd = SlotDerivation(name=populated_from, populated_from=sd.name)
        # source_cls_name = spec.class_derivations[cd.populated_from].name
        source_cls_name = cd.populated_from
        if sd.range:
            source_slot = self.source_schemaview.induced_slot(sd.populated_from, source_cls_name)
            inverted_sd.range = source_slot.range
        # if False and sd.unit_conversion:
        #    source_slot = self.source_schemaview.induced_slot(sd.populated_from, source_cls_name)
        #    inverted_sd.unit_conversion = UnitConversionConfiguration(
        #        target_unit=source_slot.unit.ucum_code
        #    )
        #
        if sd.unit_conversion:
            source_slot = self.source_schemaview.induced_slot(sd.populated_from, source_cls_name)
            target_unit = None
            target_unit_scheme = None
            if source_slot.unit is not None:
                for p in ["ucum_code", "symbol"]:
                    target_unit = getattr(source_slot.unit, p, None)
                    if target_unit is not None:
                        target_unit_scheme = p
                        break
            inverted_uc = UnitConversionConfiguration(
                target_unit=target_unit, target_unit_scheme=target_unit_scheme
            )
            # if sd.unit_conversion.target_unit:
            #    inverted_uc.source_unit = sd.unit_conversion.target_unit
            if sd.unit_conversion.source_unit_slot:
                inverted_uc.target_unit_slot = sd.unit_conversion.source_unit_slot
            if sd.unit_conversion.source_magnitude_slot:
                inverted_uc.target_magnitude_slot = sd.unit_conversion.source_magnitude_slot
            if sd.unit_conversion.target_unit:
                inverted_uc.source_unit = sd.unit_conversion.target_unit
            inverted_sd.unit_conversion = inverted_uc
        if sd.stringification:
            inverted_sd.stringification = copy(sd.stringification)
            inverted_sd.stringification.reversed = not inverted_sd.stringification.reversed
        return inverted_sd
