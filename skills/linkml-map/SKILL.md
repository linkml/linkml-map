---
name: linkml-map
description: Write, run and debug linkml-map transformation specifications, which map data from a source LinkML schema to a target LinkML schema. Use when asked to build an ingest, harmonize tables or JSON/YAML into a LinkML model, or write or fix a trans-spec.
---

# Writing linkml-map specifications

linkml-map transforms data that conforms to one LinkML schema into data that conforms to
another. You describe the mapping in a YAML *transformation specification* (trans-spec), and
the `linkml-map` CLI runs it over the data. Your job is usually to write that spec and get
the output to validate against the target schema.

## Before you write anything

Read both schemas. For each target class you will populate, note:

- its **identifier slot**, if it has one: every record needs a value for it (see Identifiers);
- its **required slots**: output that leaves them out won't validate;
- slots whose range is an **enum**, and the permissible values, meanings and aliases on it;
- slots whose range is another class: these hold **nested objects** you build in the spec.

Then look at the source: which class or table each target class comes from, and how tables
link to each other. For TSV/CSV input, each file is a table named by its file stem, so
`data/visits.tsv` is the table `visits`.

## The loop

Write the spec, check it, run it, validate the output, and repeat until the output validates.
Fix problems in the spec, never by editing the output.

```bash
linkml-map validate-spec --strict --source-schema source.yaml --target-schema target.yaml spec.yaml

linkml-map map-data --strict -T spec.yaml -s source.yaml --target-schema target.yaml \
  -f json -o out.json data/

linkml validate -s target.yaml -C Visit out.json
```

- `validate-spec` catches names that don't resolve, misspelled keys and enum literals that
  aren't permissible values before any data is read.
- Always pass `--target-schema` to `map-data`. It types the output to the target schema:
  values are coerced to each slot's range, and an enum value written as a key, meaning, title
  or alias comes out as the permissible value's key.
- `--strict` turns unknown names in expressions and unmatched enum values into errors instead
  of warnings. Add `--continue-on-error` to see every failing row instead of only the first.
- Leave out `--source-type` for a directory: each derivation reads the table it is
  `populated_from`. Pass it only for a single input file.

## Anatomy of a spec

A spec is a set of class derivations. Each names a target class, the source class or table
it is `populated_from`, and how each target slot gets its value:

```yaml
class_derivations:
  Visit:
    populated_from: visits
    joins:
      subjects:
        join_on: subject_id            # both tables have a subject_id column
    slot_derivations:
      id:
        populated_from: visit_id       # copy a column
      participant:
        populated_from: subject_id
      participant_sex:
        populated_from: subjects.gender  # a column from the joined table
      smoker:
        populated_from: smoker
        value_mappings:                # recode source values
          Y: "true"
          N: "false"
      source:
        value: clinic-intake           # a constant
      blood_pressure:                  # a nested object, built only when sbp is present
        class_derivations:
          BloodPressure:
            mint_ids: true
            slot_derivations:
              systolic:
                expr: "case(({sbp} is not None, {sbp}))"
              diastolic:
                expr: "case(({sbp} is not None, {dbp}))"
              unit:
                expr: "case(({sbp} is not None, 'mm[Hg]'))"
```

The ways to derive a slot:

| Key | Use it for |
|---|---|
| `populated_from: col` | Copying a source column or slot. `Table.col` reads a joined table. |
| `value: x` | A constant. |
| `expr: "..."` | A computed value. `{col}` reads a column; `case((cond, value), ...)` is a conditional; `str()`, `int()` and `uuid5()` are available. A missing value is `None`, and most expressions involving `None` give `None`. |
| `value_mappings` | Recoding source codes to target values. |
| `class_derivations` | Building nested objects for a slot whose range is a class. |

When the key columns differ between tables, use `source_key` and `lookup_key` instead of
`join_on`:

```yaml
joins:
  subjects:
    source_key: participant      # column in this table
    lookup_key: subject_id       # column in subjects
```

## Identifiers

If a target class has an identifier slot, each derivation must either derive it or mint it,
or the run refuses to produce output.

- **Derive it** when other records refer to this one, such as participants or visits. Use a
  natural key from the source, or build one that a referring record can rebuild, e.g.
  `uuid5("https://example.org/Visit", str({subject_id}) + ":" + str({visit_id}))`.
- **Mint it** with `mint_ids: true` when nothing refers to the record. The id is a hash of
  the record's content, so identical records get identical ids. It is not a stable
  identifier.

## Empty nested objects

A nested object whose slots all come out `None` is left out: a single-valued slot gets no
value, and a multivalued slot gets `[]`. A minted id doesn't count as content. To make a
nested object conditional, make every slot in it conditional on the same test, constants
included, as `blood_pressure` does above. A plain `value:` is never empty, so it would keep
the object.

## When output doesn't validate

- **A required slot is missing:** the source value was empty, or a name in the spec is wrong.
  Rerun `validate-spec` and check the column names against the source.
- **A value isn't a permissible value:** add the source spelling to the target enum as an
  alias, or recode it with `value_mappings`. Don't add a `range:` to the spec to silence it.
- **A nested object has only constants:** it was built for a row that had no data for it.
  Make its constants conditional, as above.
- **An expression fails on some rows:** a column was empty. Guard it with `case(...)`.

Don't add `--unrestricted-eval`. Expressions are a restricted, safe subset of Python, and a
spec that only works with unrestricted evaluation should be raised with the user.

## Reference

- Writing Specifications: https://linkml.io/linkml-map/writing-specs/
- Command-Line Reference: https://linkml.io/linkml-map/cli/
