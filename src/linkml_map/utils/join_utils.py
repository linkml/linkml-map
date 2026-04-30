"""Utilities for implicit cross-table join resolution."""

from __future__ import annotations

from linkml_runtime import SchemaView


def _is_identifier_in_either(sv: SchemaView, col: str, class_a: str, class_b: str) -> bool:
    """Check if a column is an identifier in either of two classes.

    Uses ``induced_slot`` rather than ``get_slot`` because attributes
    defined within a class carry their ``identifier`` flag on the
    class-level definition, not the top-level slot.
    """
    for cls in (class_a, class_b):
        try:
            induced = sv.induced_slot(col, cls)
            if induced and induced.identifier:
                return True
        except Exception:
            pass
    return False


def find_common_columns(sv: SchemaView, class_a: str, class_b: str) -> set[str]:
    """Find column names shared between two source classes.

    :param sv: Source schema view.
    :param class_a: First source class name.
    :param class_b: Second source class name.
    :returns: Set of column names present in both classes.
    """
    if class_a not in sv.all_classes() or class_b not in sv.all_classes():
        return set()
    a_names = {s.name for s in sv.class_induced_slots(class_a)}
    b_names = {s.name for s in sv.class_induced_slots(class_b)}
    return a_names & b_names


def pick_join_key(sv: SchemaView, class_a: str, class_b: str) -> str | None:
    """Determine the implicit join key between two source classes.

    Prefers non-identifier common columns when there is exactly one.
    Falls back to identifier columns if those are the only common columns.
    Returns None when multiple non-identifier columns are common (ambiguous).

    :param sv: Source schema view.
    :param class_a: First source class name.
    :param class_b: Second source class name.
    :returns: The join key column name, or None if no suitable key found.
    """
    common = find_common_columns(sv, class_a, class_b)

    if not common:
        return None

    non_id = {col for col in common if not _is_identifier_in_either(sv, col, class_a, class_b)}

    if len(non_id) == 1:
        return non_id.pop()
    if not non_id and common:
        return sorted(common)[0]
    # Multiple non-id common columns — can't pick automatically
    return None
