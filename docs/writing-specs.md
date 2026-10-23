# Writing Specifications

## Working with Auto-Generated Schemas

When working with schemas auto-generated from tabular data (e.g., via [schema-automator](https://github.com/linkml/schema-automator)),
foreign key relationships may not be defined. The `source_schema_patches` feature allows you to augment the source schema
with additional type information needed for cross-table lookups.

### Cross-Class Slot Lookups

Use dot notation in `populated_from` to traverse foreign key relationships:

```yaml
class_derivations:
  FlatPerson:
    populated_from: Person
    slot_derivations:
      id:
      name:
      org_name:
        populated_from: org_id.name  # Get 'name' from the Organization referenced by org_id
```

This requires:
1. The source schema defines `org_id` with `range: Organization`
2. The transformer has an `ObjectIndex` created via `transformer.index(container_data, "Container")`

### Inlined Nested Data

The same dot notation also traverses *inlined* nested objects (tree-shaped sources such
as XML, JSON Schema, OWL, or EML), walking directly into the nested structure:

```yaml
class_derivations:
  SchemaDefinition:
    populated_from: EMLDocument
    slot_derivations:
      title:
        populated_from: dataset.title  # 'title' inside the inlined 'dataset' object
```

A segment is treated as inline traversal when the source slot is declared `inlined` /
`inlined_as_list`, or when the value is a nested object at runtime. No `ObjectIndex` is
needed — the nested data is already present. Mapping each item of a multivalued inline
list through a sibling class derivation is not yet supported
([#265](https://github.com/linkml/linkml-map/issues/265)); such a path raises an error
naming the multivalued segment.

### Schema Patches for Auto-Generated Schemas

If your source schema doesn't define FK relationships (common with auto-generated schemas),
use `source_schema_patches` to add them:

```yaml
source_schema_patches:
  classes:
    Person:
      attributes:
        org_id:
          range: Organization  # Add FK relationship

class_derivations:
  FlatPerson:
    populated_from: Person
    slot_derivations:
      org_name:
        populated_from: org_id.name  # Now works with the patched schema
```

The patches use standard LinkML schema YAML structure and are applied before transformation runs.
This keeps your auto-generated schemas reproducible while adding semantic information discovered during transform design.

## Identifiers

When the target schema gives a class an identifier slot (`identifier: true`), every record
of that class needs a value for it. A class derivation provides one in one of two ways:

- **Derive it** like any other slot. Use this when other records refer to the id — a
  natural key that a referring spec can recompute, e.g.
  `uuid5("https://example.org/Visit", str({participant}) + ":" + str({visit}))`.
- **Mint it** with `mint_ids: true`. The id becomes a UUID5 hash of the record's own
  content. Use this for records nothing refers to.

If a derivation does neither, linkml-map refuses to produce output and names the class
derivation. With `--continue-on-error`, it reports the problem once, writes the records
without ids, and exits non-zero. Without a target schema there is no identifier to check.

### Turning minting on

Minting is off unless asked for. It can be turned on, or off again, at three levels;
the most specific setting wins:

```yaml
mint_ids: false              # 1. the whole specification (also the default)

class_defaults:              # 2. every derivation of a target class
  MeasurementObservation: {mint_ids: true}
  Quantity: {mint_ids: true}

class_derivations:
  MeasurementObservation:
    populated_from: lab_results
    mint_ids: false          # 3. this derivation only
    slot_derivations:
      ...
```

Abstract and mixin target classes are skipped, since they have no records of their own.
An `id` derived by an ancestor derivation (`is_a`) counts as derived.

When specifications are merged from several files, `mint_ids` and `class_defaults` must
agree across them: conflicting values are an error rather than being decided by file
order. A single file per directory holding these settings applies to everything merged
with it.

### What a minted id is

```
id = uuid5(uuid5(NAMESPACE_URL, "<target schema id>/<TargetClass>"), canonical(record))
```

The record is hashed as emitted — after derivation, without hidden slots or the id itself.
Its canonical form sorts keys; drops nulls, empty lists, and empty objects; sorts list
items unless the target slot is `list_elements_ordered`; writes every number in one
fixed-point form (so `5`, `5.0`, and `5.00` agree, and floats are rounded to 15
significant digits first); and includes nested objects with their own minted ids.

The same record always gets the same id, whatever the row order, chunking, or parallelism,
and identical records get identical ids, so duplicates are easy to find. But these are
**content hashes, not stable identifiers**: changing any emitted value — or adding a slot
that has a value — changes the id. Don't mint ids for classes other records refer to; give
those `mint_ids: false` so a forgotten derivation is caught. The background is in
[#342](https://github.com/linkml/linkml-map/issues/342).
