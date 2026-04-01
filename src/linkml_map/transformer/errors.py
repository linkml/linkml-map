"""Structured error types for transformation diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransformationError(Exception):
    """A row-level error during data transformation.

    Carries structured context so callers can report which derivation
    failed and on what input, without parsing exception strings.

    Context is added incrementally as the error propagates up the stack:

    - **``map_object``** adds ``class_derivation_name``, ``slot_derivation_name``, and ``source_row``
    - **``transform_spec``** (engine) adds ``row_index`` when an ``on_error`` callback is provided
    """

    message: str
    class_derivation_name: str | None = None
    class_populated_from: str | None = None
    slot_derivation_name: str | None = None
    slot_populated_from: str | None = None
    source_row: dict[str, Any] | None = field(default=None, repr=False)
    row_index: int | None = None
    cause: Exception | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def _format_derivation(self, label: str, name: str | None, populated_from: str | None) -> str:
        """Format a derivation field with optional source context."""
        if not name:
            return ""
        if populated_from:
            return f"{label}={name} (from {populated_from})"
        return f"{label}={name}"

    def __str__(self) -> str:
        parts = [self.message]
        class_part = self._format_derivation("class_derivation", self.class_derivation_name, self.class_populated_from)
        if class_part:
            parts.append(class_part)
        slot_part = self._format_derivation("slot_derivation", self.slot_derivation_name, self.slot_populated_from)
        if slot_part:
            parts.append(slot_part)
        if self.row_index is not None:
            parts.append(f"row={self.row_index}")
        return "; ".join(parts)
