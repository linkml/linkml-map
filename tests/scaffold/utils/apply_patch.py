from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import ( 
    ClassDefinition, EnumDefinition, Prefix, SlotDefinition, SubsetDefinition, TypeDefinition
)
import yaml

def apply_schema_patch(schemaview: SchemaView, yaml_str: str):
    """Patch a SchemaView.schema from a YAML fragment."""
    patch = yaml.safe_load(yaml_str)
    schema = schemaview.schema

    for field in ["id", "name", "description", "default_prefix"]:
        if field in patch:
            setattr(schema, field, patch[field])

    if "imports" in patch:
        for imp in patch["imports"]:
            if imp not in schema.imports:
                schema.imports.append(imp)
    
    for pname, ppatch in patch.get("prefixes", {}).items():
        schema.prefixes[pname] = Prefix(prefix_prefix=pname, prefix_reference=ppatch["prefix_reference"])

    for cname, cpatch in patch.get("classes", {}).items():
        if cname not in schema.classes:
            schema.classes[cname] = ClassDefinition(
                name=cname, **{k: v for k, v in cpatch.items() if k not in ("slots", "attributes")}
            )
        existing = schema.classes[cname]
        for slot in cpatch.get("slots", []):
            if slot not in existing.slots:
                existing.slots.append(slot)
        for attr_name, attr_def in cpatch.get("attributes", {}).items():
            existing.attributes[attr_name] = SlotDefinition(name=attr_name, **(attr_def or {}))

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

def apply_transform_patch(transform: dict, yaml_str: str):
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