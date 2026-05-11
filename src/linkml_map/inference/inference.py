"""Infer missing values in a specification."""

import warnings

from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.utils.fk_utils import resolve_fk_path


def _warn_deprecated_fields(specification: TransformationSpecification) -> None:
    """Emit ``DeprecationWarning`` for any deprecated field usage.

    Thin shim over ``validator._check_deprecated_fields`` that re-emits
    deprecation-category messages as ``DeprecationWarning`` so runtime
    callers (and any code with Python ``warnings`` filters configured)
    keep getting the same signal they always did.

    The same underlying check is consumed by static validation paths
    (``validate-spec`` and pre-flight from other CLI commands) via
    ``ValidationMessage`` records — see ``validator._check_deprecated_fields``.
    """
    from linkml_map.validator import check_deprecated_fields

    spec_dict = specification.model_dump(exclude_none=True)
    for msg in check_deprecated_fields(spec_dict):
        if msg.category == "deprecated":
            warnings.warn(msg.message, DeprecationWarning, stacklevel=3)


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
