# Command-Line Reference

The `linkml-map` CLI has the following subcommands:

- `map-data` — transform data from a source schema using a transformation specification
- `derive-schema` — derive a target schema from a source schema and a transformation specification
- `invert` — invert a transformation specification (when expressions are reversible)
- `compile` — compile a transformation specification to another representation
- `validate-spec` — structurally validate transformation specification files

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

Structurally validates a transformation specification against source and target schemas. Reports unresolved class/slot references, deprecated fields, and other issues.

```bash
linkml-map validate-spec \
  --source-schema source/personinfo.yaml \
  --target-schema target/agent.yaml \
  transform/personinfo-to-agent.transform.yaml
```

Use `--strict` to treat warnings as errors. Supports validating multiple files or directories of specs in a single call.

## compile

Compiles a transformation specification to another representation.

```bash
linkml-map compile --target python -T transform.yaml -s source.yaml
linkml-map compile --target markdown -T transform.yaml -s source.yaml
```

Currently supported `--target` values are `python` (default) and `markdown`. A SQL compilation backend (`SQLCompiler` / `DuckDBTransformer`) exists for programmatic use but is not yet exposed through the `compile` subcommand.
