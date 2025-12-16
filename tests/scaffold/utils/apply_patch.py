"""Test utilities for patching schemas and transform specs."""

import yaml
from linkml_runtime import SchemaView

from linkml_map.utils.schema_patch import apply_schema_patch as _apply_schema_patch


def apply_schema_patch(schemaview: SchemaView, yaml_str: str) -> None:
    """
    Patch a SchemaView.schema from a YAML string.

    Test convenience wrapper that accepts YAML strings for readability.
    """
    _apply_schema_patch(schemaview, yaml.safe_load(yaml_str))


def apply_transform_patch(transform: dict, yaml_str: str) -> dict:
    """Merge a YAML fragment into the scaffold['transform_spec']."""
    patch = yaml.safe_load(yaml_str) or {}

    def merge(d, p):
        for k, v in p.items():
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                merge(d[k], v)
            elif isinstance(v, list) and isinstance(d.get(k), list):
                d[k].extend(v)
            else:
                d[k] = v

    merge(transform, patch)
    return transform
