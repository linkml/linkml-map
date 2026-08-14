"""Pivot (MELT / UNMELT) operations for EAV-shaped data.

Extracted from ``ObjectTransformer`` (issue #304). These never touched instance
state beyond ``target_schemaview``, which the two functions that need it now take
explicitly, so they are plain module functions rather than methods.

``perform_pivot_operation`` and ``perform_melt`` are the entry points the
transformer calls; the rest are internal steps.
"""

import logging
from typing import Any

from linkml_runtime import SchemaView

from linkml_map.datamodel.transformer_model import (
    ClassDerivation,
    PivotDirectionType,
    PivotOperation,
    SlotDerivation,
)

logger = logging.getLogger(__name__)

DICT_OBJ = dict[str, Any]


def perform_pivot_operation(
    pivot_op: PivotOperation,
    source_obj: DICT_OBJ,
    class_deriv: ClassDerivation,
    sv: SchemaView,
    source_type: str,
    target_sv: SchemaView | None = None,
) -> DICT_OBJ | list[DICT_OBJ]:
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
        return _perform_unmelt(pivot_op, source_obj, class_deriv, sv, source_type, target_sv)
    elif pivot_op.direction == PivotDirectionType.MELT:
        return perform_melt(pivot_op, source_obj, class_deriv, target_sv)
    else:
        msg = f"Unknown pivot direction: {pivot_op.direction}"
        raise ValueError(msg)


def _perform_unmelt(
    pivot_op: PivotOperation,
    source_obj: DICT_OBJ,
    class_deriv: ClassDerivation,
    sv: SchemaView,
    source_type: str,
    target_sv: SchemaView | None = None,
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
        return _unmelt_single_record(pivot_op, source_obj, variable_slot, value_slot, unit_slot, template, target_sv)

    # Otherwise, look for a collection of EAV records in the source
    # Try to find a multivalued slot containing EAV records
    for slot_name, slot_value in source_obj.items():
        if isinstance(slot_value, list) and len(slot_value) > 0:
            first_item = slot_value[0]
            if isinstance(first_item, dict) and variable_slot in first_item:
                return _unmelt_collection(pivot_op, slot_value)

    # Fallback: treat source_obj as a single EAV record
    return _unmelt_single_record(pivot_op, source_obj, variable_slot, value_slot, unit_slot, template, target_sv)


def _unmelt_single_record(
    pivot_op: PivotOperation,
    record: DICT_OBJ,
    variable_slot: str,
    value_slot: str,
    unit_slot: str | None,
    template: str,
    target_sv: SchemaView | None = None,
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
    if pivot_op.unmelt_to_class and target_sv:
        valid_slots = [s.name for s in target_sv.class_induced_slots(pivot_op.unmelt_to_class)]
        if pivot_op.unmelt_to_slots:
            valid_slots = [s for s in valid_slots if s in pivot_op.unmelt_to_slots]

        if target_slot_name not in valid_slots:
            logger.warning(
                f"Generated slot name '{target_slot_name}' not in valid slots for class '{pivot_op.unmelt_to_class}'"
            )

    result[target_slot_name] = value
    return result


def _unmelt_collection(
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


def perform_melt(
    pivot_op: PivotOperation,
    source_obj: DICT_OBJ,
    slot_derivation: SlotDerivation | None = None,
    target_sv: SchemaView | None = None,
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
    elif pivot_op.unmelt_to_class and target_sv:
        # Infer from target class
        slots_to_melt = [s.name for s in target_sv.class_induced_slots(pivot_op.unmelt_to_class)]
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
