"""Infer missing values in a specification."""

from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.utils.fk_utils import resolve_fk_path


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
                if "." in populated_from_slot:
                    # cd.joins may be empty here (join synthesis runs later).
                    table_name, field_path = populated_from_slot.split(".", 1)
                    joined_class = None
                    if cd.joins and table_name in cd.joins:
                        joined_class = cd.joins[table_name].class_named or table_name
                    elif table_name in source_schemaview.all_classes():
                        joined_class = table_name
                    if joined_class and joined_class in source_schemaview.all_classes():
                        induced_names = {s.name for s in source_schemaview.class_induced_slots(joined_class)}
                        if field_path in induced_names:
                            source_induced_slot = source_schemaview.induced_slot(field_path, joined_class)
                            source_induced_slot_range = source_induced_slot.range

                if source_induced_slot_range is None:
                    fk_resolution = resolve_fk_path(source_schemaview, cd.populated_from, populated_from_slot)
                    if fk_resolution:
                        if not fk_resolution.final_slot:
                            continue
                        source_induced_slot_range = fk_resolution.final_slot.range
                    elif "." in populated_from_slot:
                        # Unresolvable Table.col: skip (bare-slot lookup would raise, #279).
                        continue
                    else:
                        source_induced_slot = source_schemaview.induced_slot(populated_from_slot, cd.populated_from)
                        source_induced_slot_range = source_induced_slot.range

                for range_cd in specification.class_derivations:
                    if range_cd.populated_from == source_induced_slot_range:
                        sd.range = range_cd.name
