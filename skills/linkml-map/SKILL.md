---
name: linkml-map
description: Write and run linkml-map transformation specifications that map data from one LinkML schema to another, such as ingesting TSV/CSV tables or JSON/YAML into a target model. Use when asked to write an ingest, a mapping or a trans-spec between LinkML schemas, or to debug one.
---

# Writing linkml-map specifications

A transformation specification (trans-spec) is a YAML file of class derivations: each one
names a target class, the source class or table it is `populated_from`, and how each target
slot is derived. The `linkml-map` CLI runs it over data.

Full reference: https://linkml.io/linkml-map/writing-specs/ and
https://linkml.io/linkml-map/cli/.

## Workflow

1. **Read both schemas.** Know each target class's required slots, identifier slot,
   enum ranges and inlined classes before writing anything.
2. **Write the spec.** Start from one class derivation per target class:

   ```yaml
   class_derivations:
     Participant:
       populated_from: subjects        # source class, or table name for TSV/CSV input
       slot_derivations:
         id:
           populated_from: subject_id
         age:
           expr: "{age_at_enrollment}"
         sex:
           populated_from: gender
   ```

3. **Check it before running:**

   ```bash
   linkml-map validate-spec --strict --source-schema source.yaml --target-schema target.yaml spec.yaml
   ```

4. **Run it, typed to the target schema:**

   ```bash
   linkml-map map-data --strict -T spec.yaml -s source.yaml --target-schema target.yaml \
     --source-type subjects -f json -o out.json data/
   ```

5. **Validate the output against the target schema**, and fix the spec rather than the output:

   ```bash
   linkml validate -s target.yaml -C Participant out.json
   ```

## Rules that save a round trip

- **Always pass `--target-schema`.** Values are then coerced to the target slot's range, and
  enum values given as a key, `meaning`, title or alias resolve to the permissible value key.
  Don't add a spec `range:` that fights the target's.
- **Identifiers must be derived or minted.** If a target class has an identifier slot, derive
  it from a natural key when other records refer to it; set `mint_ids: true` only for records
  nothing refers to. Otherwise the run refuses to produce output.
- **Joins.** For a directory of tables, reference another table's column as
  `{Table.column}`; add a `joins:` block when the key columns are named differently.
- **Conditional nested objects.** A nested object whose slots all come out None is left out
  (None for a single-valued slot, `[]` for a multivalued one). To make one conditional, make
  every slot in it conditional on the same test with `case(...)`, constants included.
- **Leave `--unrestricted-eval` off.** Expressions are a safe Python subset; a spec that
  needs full Python should say so to the user.
- **`--continue-on-error`** reports every failing row instead of stopping at the first;
  use it to see the whole picture on real data.
