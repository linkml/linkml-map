"""Infer missing values in a specification."""

import warnings

from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.utils.fk_utils import resolve_fk_path


def _warn_deprecated_sources(specification: TransformationSpecification) -> None:
    """Emit deprecation warnings for any use of the ``sources`` field.

    Checks class derivations, slot derivations, enum derivations, and
    permissible value derivations.  The ``sources`` field is deprecated
    in favor of list-based ``populated_from``.  Warnings are collapsed
    to one per derivation type to avoid noise.
    """
    counts: dict[str, list[str]] = {
        "ClassDerivation": [],
        "SlotDerivation": [],
        "EnumDerivation": [],
        "PermissibleValueDerivation": [],
    }
    for cd in specification.class_derivations:
        if cd.sources:
            counts["ClassDerivation"].append(cd.name)
        for sd in cd.slot_derivations.values():
            if sd.sources:
                counts["SlotDerivation"].append(sd.name)
    for ed in specification.enum_derivations.values():
        if ed.sources:
            counts["EnumDerivation"].append(ed.name)
        for pvd in ed.permissible_value_derivations.values():
            if pvd.sources:
                counts["PermissibleValueDerivation"].append(pvd.name)

    for deriv_type, names in counts.items():
        if names:
            names_str = ", ".join(names[:5])
            suffix = f" (and {len(names) - 5} more)" if len(names) > 5 else ""
            warnings.warn(
                f"{len(names)} {deriv_type}(s) use 'sources', which is deprecated: "
                f"{names_str}{suffix}. "
                f"Use 'populated_from' (which now accepts a list) instead. "
                f"'sources' will be removed in a future version.",
                DeprecationWarning,
                stacklevel=3,
            )


def induce_missing_values(specification: TransformationSpecification, source_schemaview: SchemaView) -> None:
    """
    Infer missing values in a specification.

    Currently only uses copy directives.

    :param specification:
    :param source_schemaview:
    :return:
    """
    for cd in specification.class_derivations:
        if not cd.populated_from:
            cd.populated_from = cd.name
    _warn_deprecated_sources(specification)

    for cd in specification.class_derivations:
        for sd in cd.slot_derivations.values():
            if sd.derived_from:
                warnings.warn(
                    f"SlotDerivation '{sd.name}' uses 'derived_from', which is deprecated "
                    f"and ignored by the runtime. Use 'populated_from' instead. "
                    f"'derived_from' will be removed in a future version.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            if sd.object_derivations:
                # skip inference for object derivations, inferences come from class derivation later
                # TODO: we may need to do the inference for the internal class slots
                continue
            # for null mappings, assume that the slot is copied from the same slot in the source
            # TODO: decide if this is the desired behavior
            if sd.populated_from is None and sd.expr is None:
                sd.populated_from = sd.name
            if sd.range is None and sd.value is not None:
                sd.range = "string"
            if not sd.range and sd.populated_from:
                # auto-populate range field
                if cd.populated_from not in source_schemaview.all_classes():
                    continue

                populated_from_slot = sd.populated_from

                source_induced_slot_range = None
                if "." in populated_from_slot and cd.joins:
                    table_name, field_path = populated_from_slot.split(".", 1)
                    if table_name in cd.joins:
                        joined_class = cd.joins[table_name].class_named or table_name
                        if joined_class not in source_schemaview.all_classes():
                            continue
                        if field_path in source_schemaview.class_induced_slots(joined_class):
                            source_induced_slot = source_schemaview.induced_slot(field_path, joined_class)
                            source_induced_slot_range = source_induced_slot.range
                        else:
                            continue

                if source_induced_slot_range is None:
                    fk_resolution = resolve_fk_path(source_schemaview, cd.populated_from, populated_from_slot)
                    if fk_resolution:
                        if not fk_resolution.final_slot:
                            continue
                        source_induced_slot_range = fk_resolution.final_slot.range
                    else:
                        source_induced_slot = source_schemaview.induced_slot(populated_from_slot, cd.populated_from)
                        source_induced_slot_range = source_induced_slot.range

                for range_cd in specification.class_derivations:
                    if range_cd.populated_from == source_induced_slot_range:
                        sd.range = range_cd.name
