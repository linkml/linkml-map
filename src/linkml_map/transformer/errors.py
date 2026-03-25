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
    slot_derivation_name: str | None = None
    source_row: dict[str, Any] | None = field(default=None, repr=False)
    row_index: int | None = None
    cause: Exception | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.class_derivation_name:
            parts.append(f"class_derivation={self.class_derivation_name}")
        if self.slot_derivation_name:
            parts.append(f"slot_derivation={self.slot_derivation_name}")
        if self.row_index is not None:
            parts.append(f"row={self.row_index}")
        return "; ".join(parts)
