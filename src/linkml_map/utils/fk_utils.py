"""Utilities for resolving foreign key paths in LinkML schemas."""

from typing import NamedTuple, Optional

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinition


class FKResolution(NamedTuple):
    """Result of resolving a dot-notation FK path."""

    fk_slot_name: str
    target_class: str
    remaining_path: str
    final_slot: Optional[SlotDefinition]


def resolve_fk_path(
    schemaview: SchemaView, source_class: str, path: str
) -> Optional[FKResolution]:
    """
    Resolve a dot-notation FK path to its components.

    Given a path like "org_id.name" and source class "Person", resolves:
    - target_class: the class referenced by the FK (Organization)
    - remaining_path: the path within that class (name)
    - final_slot: SlotDefinition for the final attribute

    Args:
        schemaview: The schema view to use for resolution
        source_class: The class containing the FK slot
        path: Dot-notation path (e.g., "org_id.name")

    Returns:
        FKResolution with resolved components, or None if not an FK path
    """
    if "." not in path:
        return None

    fk_slot_name, remaining_path = path.split(".", 1)

    try:
        fk_slot = schemaview.induced_slot(fk_slot_name, source_class)
    except Exception:
        return None

    target_class = fk_slot.range
    if not target_class or target_class not in schemaview.all_classes():
        return None

    # Walk the remaining path to find the final slot
    current_class = target_class
    path_segments = remaining_path.split(".")
    final_slot = None

    for i, attr in enumerate(path_segments):
        try:
            slot = schemaview.induced_slot(attr, current_class)
        except Exception:
            break

        if i == len(path_segments) - 1:
            final_slot = slot
        elif slot.range and slot.range in schemaview.all_classes():
            current_class = slot.range
        else:
            break

    return FKResolution(fk_slot_name, target_class, remaining_path, final_slot)
