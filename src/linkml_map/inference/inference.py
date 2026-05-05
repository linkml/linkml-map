"""Infer missing values in a specification."""

import warnings

from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.utils.fk_utils import resolve_fk_path


def _warn_deprecated_fields(specification: TransformationSpecification) -> None:
    """Emit deprecation warnings for use of deprecated fields.

    Checks for ``sources`` (deprecated in favor of ``populated_from``)
    and ``derived_from`` (deprecated, unused by runtime).
    ``object_derivations`` warnings are emitted during normalization
    (see ``Transformer._normalize_slot_class_derivations``).
    Warnings are collapsed to one per field per derivation type to avoid noise.
    """
    sources_counts: dict[str, list[str]] = {
        "ClassDerivation": [],
        "SlotDerivation": [],
        "EnumDerivation": [],
        "PermissibleValueDerivation": [],
    }
    derived_from_names: list[str] = []

    for cd in specification.class_derivations:
        if cd.sources:
            sources_counts["ClassDerivation"].append(cd.name)
        for sd in cd.slot_derivations.values():
            if sd.sources:
                sources_counts["SlotDerivation"].append(sd.name)
            if sd.derived_from:
                derived_from_names.append(sd.name)
    for ed in specification.enum_derivations.values():
        if ed.sources:
            sources_counts["EnumDerivation"].append(ed.name)
        for pvd in ed.permissible_value_derivations.values():
            if pvd.sources:
                sources_counts["PermissibleValueDerivation"].append(pvd.name)

    for deriv_type, names in sources_counts.items():
        if names:
            names_str = ", ".join(names[:5])
            suffix = f" (and {len(names) - 5} more)" if len(names) > 5 else ""
            warnings.warn(
                f"{len(names)} {deriv_type}(s) use 'sources', which is deprecated: "
                f"{names_str}{suffix}. "
                f"Use 'populated_from' instead. "
                f"'sources' will be removed in a future version.",
                DeprecationWarning,
                stacklevel=3,
            )

    if derived_from_names:
        names_str = ", ".join(derived_from_names[:5])
        suffix = f" (and {len(derived_from_names) - 5} more)" if len(derived_from_names) > 5 else ""
        warnings.warn(
            f"{len(derived_from_names)} SlotDerivation(s) use 'derived_from', "
            f"which is deprecated and ignored by the runtime: "
            f"{names_str}{suffix}. "
            f"This field can be removed — source slot dependencies are "
            f"derivable from 'expr'. "
            f"'derived_from' will be removed in a future version.",
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
    _warn_deprecated_fields(specification)

    for cd in specification.class_derivations:
        for sd in cd.slot_derivations.values():
            if sd.class_derivations:
                # skip inference for nested class derivations; inferences come from
                # the class derivation later
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
