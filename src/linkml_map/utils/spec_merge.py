"""Utilities for loading and merging multiple transformation specification files.

Supports loading specs from multiple files or directories, handling both
standard ``TransformationSpecification`` dicts and the compact list-of-blocks
format used by per-variable sub-specs::

    # Standard format
    class_derivations:
      - EntityName:
          populated_from: ...

    # List-of-blocks format (each item is a partial spec)
    - class_derivations:
        EntityName:
          populated_from: ...
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def resolve_spec_paths(paths: tuple[str | Path, ...]) -> list[Path]:
    """Resolve a mix of file paths and directories to a flat list of YAML files.

    Directories are recursively searched for ``*.yaml`` and ``*.yml`` files.
    Files are included directly.

    :param paths: File paths or directory paths.
    :returns: Sorted list of resolved YAML file paths.
    :raises FileNotFoundError: If a path does not exist.
    """
    resolved: list[Path] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            msg = f"Spec path does not exist: {path}"
            raise FileNotFoundError(msg)
        if path.is_dir():
            resolved.extend(sorted([*path.rglob("*.yaml"), *path.rglob("*.yml")]))
        else:
            resolved.append(path)
    return resolved


def load_spec_file(path: Path) -> list[dict[str, Any]]:
    """Load a YAML spec file and return a list of spec dicts.

    Handles two formats:

    1. A single dict (standard ``TransformationSpecification``).
    2. A YAML list of partial spec dicts (compact sub-spec format).

    :param path: Path to the YAML file.
    :returns: A list of one or more spec dicts.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    logger.warning("Skipping %s: expected dict or list, got %s", path, type(data).__name__)
    return []


def merge_spec_dicts(spec_dicts: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge multiple spec dicts into a single TransformationSpecification dict.

    Merge strategy:

    - ``class_derivations``: appended in order (list or dict values are
      accumulated into a single list).
    - ``enum_derivations``: merged by name (dict union). Raises on duplicate
      enum names with conflicting definitions.
    - ``slot_derivations``: merged by name (dict union). Raises on duplicate
      slot names with conflicting definitions.
    - Scalar fields (``title``, ``source_schema``, etc.): first non-None value
      wins.

    :param spec_dicts: A list of raw spec dicts to merge.
    :returns: A single merged spec dict.
    :raises ValueError: If enum or slot derivations conflict on the same name.
    """
    if not spec_dicts:
        return {}
    if len(spec_dicts) == 1:
        return spec_dicts[0]

    merged: dict[str, Any] = {}
    merged_class_derivations: list = []
    merged_enum_derivations: dict[str, Any] = {}
    merged_slot_derivations: dict[str, Any] = {}

    _COLLECTION_KEYS = {"class_derivations", "enum_derivations", "slot_derivations"}

    for spec in spec_dicts:
        # Accumulate class_derivations
        cd = spec.get("class_derivations")
        if cd is not None:
            if isinstance(cd, list):
                merged_class_derivations.extend(cd)
            elif isinstance(cd, dict):
                for name, body in cd.items():
                    merged_class_derivations.append({name: body} if body else {name: {}})

        # Union enum_derivations by name
        ed = spec.get("enum_derivations")
        if isinstance(ed, dict):
            for name, body in ed.items():
                if name in merged_enum_derivations and merged_enum_derivations[name] != body:
                    msg = f"Conflicting enum_derivations for '{name}'"
                    raise ValueError(msg)
                merged_enum_derivations[name] = body

        # Union slot_derivations by name
        sd = spec.get("slot_derivations")
        if isinstance(sd, dict):
            for name, body in sd.items():
                if name in merged_slot_derivations and merged_slot_derivations[name] != body:
                    msg = f"Conflicting slot_derivations for '{name}'"
                    raise ValueError(msg)
                merged_slot_derivations[name] = body

        # Scalar fields: first non-None wins
        for key, value in spec.items():
            if key not in _COLLECTION_KEYS and key not in merged and value is not None:
                merged[key] = value

    if merged_class_derivations:
        merged["class_derivations"] = merged_class_derivations
    if merged_enum_derivations:
        merged["enum_derivations"] = merged_enum_derivations
    if merged_slot_derivations:
        merged["slot_derivations"] = merged_slot_derivations

    return merged


def load_and_merge_specs(paths: tuple[str | Path, ...]) -> dict[str, Any]:
    """Load spec files from paths/directories and merge into a single spec dict.

    :param paths: File paths or directory paths to load.
    :returns: A single merged spec dict.
    :raises FileNotFoundError: If a path does not exist.
    :raises ValueError: If no YAML files are found or derivations conflict.
    """
    file_paths = resolve_spec_paths(paths)
    if not file_paths:
        msg = "No YAML files found in the provided paths"
        raise ValueError(msg)

    all_dicts: list[dict[str, Any]] = []
    for fp in file_paths:
        all_dicts.extend(load_spec_file(fp))

    if not all_dicts:
        msg = "No valid spec dicts found in the provided files"
        raise ValueError(msg)

    return merge_spec_dicts(all_dicts)
