# Command-Line Reference

The `linkml-map` CLI has the following subcommands:

- `map-data` — transform data from a source schema using a transformation specification
- `derive-schema` — derive a target schema from a source schema and a transformation specification
- `invert` — invert a transformation specification (renames, unit conversions and stringification; expressions can't be inverted)
- `compile` — compile a transformation specification to another representation
- `validate-spec` — check transformation specification files against their source and target schemas

Run any subcommand with `--help` for full options.

## map-data

Transforms (maps) data from a source schema to a target schema. This could range from a simple data dictionary mapping
through to a complex mapping.

```bash
cd tests/input/examples/personinfo_basic
linkml-map map-data --unrestricted-eval \
  -T transform/personinfo-to-agent.transform.yaml \
  -s source/personinfo.yaml \
  data/Container-001.yaml
```

Options that change what a run does:

- `-T` can be repeated, and can name a directory. All the specs found are merged into one
  before the run; `--emit-spec FILE` writes the merged result. `--entity NAME` runs only the
  class derivations for one target class.
- `--target-schema` types the output to the target schema. Values are coerced to each target
  slot's range, enum values are resolved to permissible values, and every class with an
  identifier slot must derive or mint its id (see [Identifiers](writing-specs.md#identifiers)).
  Without it, only a `range:` written in the spec coerces values.
- `--strict` turns a name in an expression that isn't a source slot, or an enum value that
  matches no permissible value (or more than one), into an error instead of a warning.
  Recommended for real data.
- `--continue-on-error` reports every failing row at the end instead of stopping at the
  first, and exits non-zero if any failed.
- `--unrestricted-eval` allows full Python in expressions. Leave it off unless a spec needs it.
- `-F FILE` adds the `@safe_function` functions in a Python file to the expression namespace.

Before mapping, `map-data` runs the `validate-spec` checks and prints any problems as
warnings; they don't stop the run.

### Tabular Data Support (TSV/CSV)

The `map-data` command supports tabular data files (TSV and CSV) as input, enabling transformations
on large datasets with streaming output.

**Single TSV/CSV file:**

```bash
linkml-map map-data \
  -T transform.yaml \
  -s source_schema.yaml \
  --source-type Person \
  people.tsv
```

**Directory of data files:**

When transforming data from multiple source types, organize your data in a directory with files
named after the source type (e.g., `Person.tsv`, `Organization.csv`):

```bash
linkml-map map-data \
  -T transform.yaml \
  -s source_schema.yaml \
  -f jsonl \
  -o output.jsonl \
  ./data/
```

**Output formats:**

The `-f/--output-format` option supports:
- `yaml` - YAML format (default)
- `json` - JSON array
- `jsonl` - JSON Lines (one object per line)
- `tsv` - Tab-separated values
- `csv` - Comma-separated values
- `parquet` - Apache Parquet, with nested fields preserved as columns
- `duckdb` - a DuckDB database file, one table per run

Output format can also be inferred from the output file extension.

**Streaming for large files:**

For large datasets, use `--chunk-size` to control memory usage:

```bash
linkml-map map-data \
  -T transform.yaml \
  -s schema.yaml \
  --source-type Person \
  --chunk-size 1000 \
  -f jsonl \
  large_dataset.tsv
```

### Multi-Format Output

Use `-O`/`--additional-output` to write multiple output formats simultaneously
from a single transformation pass:

```bash
linkml-map map-data \
  -T transform.yaml \
  -s schema.yaml \
  -f jsonl \
  -o output.jsonl \
  -O output.tsv \
  -O output.json \
  people.tsv
```

The primary output uses `-f`/`-o` as usual. Each `-O` flag adds an additional
output file whose format is inferred from the file extension (`.json`, `.jsonl`,
`.yaml`, `.yml`, `.tsv`, `.csv`, `.parquet`, `.duckdb`). All outputs are written
in a single streaming pass.

### Columnar Output

`parquet` and `duckdb` write a columnar artifact rather than text. Unlike `tsv`
and `csv`, which flatten to one row of scalars, these keep nested structure: a
nested object becomes a `STRUCT` column and a list of them a `STRUCT[]`, so a
consumer reads a nested field with a column access instead of a join.

```bash
linkml-map map-data \
  -T transform.yaml \
  -s schema.yaml \
  --source-type Person \
  -o agents.parquet \
  data/Person.tsv
```

DuckDB output writes one table per run, named by `--table-name` and defaulting
to the output file's stem. Pointing several runs at the same `.duckdb` path
builds up a database covering multiple target classes:

```bash
linkml-map map-data -T transform.yaml -s schema.yaml \
  --source-type Person --table-name person -o study.duckdb data/Person.tsv
linkml-map map-data -T transform.yaml -s schema.yaml \
  --source-type Measurement --table-name measurement -o study.duckdb data/Measurement.tsv
```

Both formats also work as `-O` targets alongside a text primary output. Neither
adds a dependency: `duckdb` is already required by the join engine.

## derive-schema

Derives a target schema (the "profile") implied by the transformation specification.

```bash
cd tests/input/examples/personinfo_basic
linkml-map derive-schema -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml
```

## validate-spec

Checks a transformation specification before it runs. It reports:

- spec structure that doesn't match the transformation data model, and deprecated fields
- class, slot and `populated_from` references, and names used in expressions, that don't
  resolve against the source schema
- target classes and slots that don't exist in the target schema
- `joins` and `is_a` references that don't resolve
- arithmetic on slots that hold strings
- `value:` literals and `value_mappings` targets that aren't permissible values of the
  target slot's enum
- a spec `range:` that overrides the target slot's range so that values won't be coerced
  or resolved to it

The source and target schemas come from `--source-schema` and `--target-schema`, or from
the spec's own `source_schema` and `target_schema` fields when they are paths or URLs.

```bash
linkml-map validate-spec \
  --source-schema source/personinfo.yaml \
  --target-schema target/agent.yaml \
  transform/personinfo-to-agent.transform.yaml
```

Use `--strict` to treat warnings as errors. Supports validating multiple files or directories of specs in a single call; add `--merge` to validate them as one merged spec, as `map-data` would run them.

## compile

Compiles a transformation specification to another representation.

```bash
linkml-map compile --target python -T transform.yaml -s source.yaml
linkml-map compile --target markdown -T transform.yaml -s source.yaml
```

Currently supported `--target` values are `python` (default) and `markdown`. A SQL compilation backend (`SQLCompiler` / `DuckDBTransformer`) exists for programmatic use but is not yet exposed through the `compile` subcommand.
