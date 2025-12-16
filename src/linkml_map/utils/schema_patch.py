"""Utilities for patching LinkML schemas."""

from typing import Any

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import (
    ClassDefinition,
    EnumDefinition,
    Prefix,
    SlotDefinition,
    SubsetDefinition,
    TypeDefinition,
)


def apply_schema_patch(schemaview: SchemaView, patch: dict[str, Any]) -> None:
    """
    Apply a patch to a SchemaView's schema.

    This is useful for augmenting auto-generated schemas with additional
    information such as foreign key relationships (range specifications)
    that are discovered during transformation design.

    :param schemaview: The SchemaView to patch
    :param patch: A dict using LinkML schema YAML structure
    """
    if patch is None:
        return

    schema = schemaview.schema

    for field in ["id", "name", "description", "default_prefix"]:
        if field in patch:
            setattr(schema, field, patch[field])

    if "imports" in patch:
        for imp in patch["imports"]:
            if imp not in schema.imports:
                schema.imports.append(imp)

    for pname, ppatch in patch.get("prefixes", {}).items():
        schema.prefixes[pname] = Prefix(
            prefix_prefix=pname, prefix_reference=ppatch["prefix_reference"]
        )

    for cname, cpatch in patch.get("classes", {}).items():
        if cname not in schema.classes:
            schema.classes[cname] = ClassDefinition(
                name=cname,
                **{k: v for k, v in cpatch.items() if k not in ("slots", "attributes")},
            )
        existing = schema.classes[cname]
        for slot in cpatch.get("slots", []):
            if slot not in existing.slots:
                existing.slots.append(slot)
        for attr_name, attr_def in cpatch.get("attributes", {}).items():
            if attr_name not in existing.attributes:
                existing.attributes[attr_name] = SlotDefinition(
                    name=attr_name, **(attr_def or {})
                )
            else:
                existing_attr = existing.attributes[attr_name]
                for field, value in (attr_def or {}).items():
                    setattr(existing_attr, field, value)

    simple_definitions = {
        "slots": SlotDefinition,
        "enums": EnumDefinition,
        "types": TypeDefinition,
        "subsets": SubsetDefinition,
    }

    for key, cls in simple_definitions.items():
        for name, patch_data in patch.get(key, {}).items():
            if name not in getattr(schema, key):
                getattr(schema, key)[name] = cls(name=name, **patch_data)
            else:
                existing = getattr(schema, key)[name]
                for field, value in patch_data.items():
                    setattr(existing, field, value)
