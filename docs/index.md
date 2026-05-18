# LinkML-Map

LinkML Map is a framework for specifying and executing declarative mappings between data models.

The core of LinkML Map is the **TransformationSpecification** — a YAML-based language for describing
how to map one data model to another. This specification is independent of how the transformation
is executed or what format the data lives in.

Features:

- YAML-based lightweight transformation syntax
- Python library for executing mappings on data files
- Streaming support for large tabular datasets (TSV/CSV)
- Multiple text serialization formats (YAML, JSON, JSONL, TSV, CSV)
- Derivation of target (implicit) schemas, allowing easy customization of data models (*profiling*)
- Simple YAML dictionaries for simple mappings
- Automatic unit conversion
- Use of subset of Python to specify complex mappings
- Visualizations of mappings
- Mappings are reversible (provided all expressions used are reversible)
- Compatibility with SSSOM

## Architecture

The TransformationSpecification acts as a declarative intermediate representation that can be
interpreted by different execution backends:

- **ObjectTransformer** (Python) — interprets the spec row-by-row, supports the full feature set
  including Python expressions, unit conversion, and cross-class lookups.
- **SQLCompiler / DuckDBTransformer** (SQL) — compiles the spec to SQL for set-based execution.
  This backend is **experimental** and supports a limited subset of the specification today.
  See the [SQL Compilation tutorial](examples/Tutorial-SQLCompiler.ipynb) for current capabilities.

The output serialization formats (YAML, JSON, JSONL, TSV, CSV) are intentionally limited to
text-based representations of transformed data. For loading results into analytical stores
(DuckDB, Parquet, databases), use the appropriate downstream tool — e.g., DuckDB's native
`read_json()` or `read_csv()` functions work directly on linkml-map output files.

This documentation is available at:

- [linkml.io/linkml-map/](https://linkml.io/linkml-map/)

Status:

The transformation data model is not yet fully stable, and may be subject to change.
Not all parts of the model are implemented in the reference Python framework.

## Quick Start

### Install

```bash
uv add linkml-map
# or: pip install linkml-map
```

Verify the install:

```bash
linkml-map --help
```

### Run the included example

The repository includes a `personinfo_basic` example that transforms `Person` records into `Agent` records:

```bash
cd tests/input/examples/personinfo_basic
linkml-map map-data --unrestricted-eval \
  -T transform/personinfo-to-agent.transform.yaml \
  -s source/personinfo.yaml \
  data/Container-001.yaml
```

This produces:

```yaml
agents:
- id: P:001
  label: fred bloggs
  age: 33 years
  primary_email: fred.bloggs@example.com
  driving_since: 2014-03-31
  first_known_event: 1990-01-01
  current_address:
    address_of: foo
    street: 1 oak street
    city: oaktown
  has_familial_relationships:
  - type: SIBLING_OF
    related_to: P:002
  - type: CHILD_OF
    related_to: P:003
...
```

This example uses Python-rich expressions (filtering over multivalued slots) which require `--unrestricted-eval`. Most transformation specifications use simpler expressions and don't need this flag.

## Basic idea

Given the LinkML schema

```yaml
id: https://w3id.org/linkml/examples/personinfo
name: personinfo
prefixes:
  linkml: https://w3id.org/linkml/
  personinfo: https://w3id.org/linkml/examples/personinfo
imports:
  - linkml:types
default_range: string
default_prefix: personinfo

classes:
  Person:
    attributes:
      id:
      given_name:
      family_name:
      aliases:
        multivalued: true
      height_in_cm:
        range: float
        unit:
          ucum_code: cm
      age_in_years:
        range: integer
```

and an object that conforms to it, e.g.:

```yaml
given_name: Jane
family_name: Doe
height_in_cm: 172.0
age_in_years: 33
aliases: [Janey, Janie]
```

Define a mapping in YAML:

```yaml
class_derivations:
  Individual:
    populated_from: Person
    slot_derivations:
      name:
        expr: "{given_name} + ' ' + {family_name}"
        description: Concatenating given and family names
          note this is a bad assumption for names in general,
          this is just for demonstration
      height_in_meters:
        populated_from: height_in_cm
        unit_conversion:
          target_unit: m
      aliases:
        populated_from: aliases
        stringification:
          delimiter: '|'
```

The schema mapping (aka [TransformationSpecification](schema/TransformationSpecification.md)) specifies how to transform the data model.

The schema mapping is a collection of one or more [ClassDerivation](schema/ClassDerivation.md) objects,
which themselves consist of one or more [SlotDerivation](schema/SlotDerivation.md) objects.

A single specification can contain derivations for multiple target classes, and multiple
derivations can target the same class (their slot derivations are merged), producing:

```yaml
name: Jane Doe
height_in_meters: 1.72
aliases: Janey|Janie
```

## Transform your own data

You need three things:

1. **A source schema** — a LinkML schema describing your input data
2. **A transformation specification** — the YAML file describing how source slots map to target slots
3. **Your data** — files in YAML, JSON, JSONL, TSV, or CSV that conform to the source schema

For one-off runs, invoke `linkml-map map-data` directly (see [Running the code](#running-the-code) below). For production pipelines, the recommended pattern is to glue validation and transformation together with `make`:

```makefile
RUN := uv run

SOURCE_SCHEMA := source/personinfo.yaml
TARGET_SCHEMA := target/agent.yaml
TRANSFORM     := transform/personinfo-to-agent.transform.yaml
INPUT_DIR     := data/
OUTPUT        := output/agents.yaml

.PHONY: validate transform

validate:
	$(RUN) linkml validate -s $(SOURCE_SCHEMA) $(INPUT_DIR)
	$(RUN) linkml-map validate-spec \
		--source-schema $(SOURCE_SCHEMA) \
		--target-schema $(TARGET_SCHEMA) \
		$(TRANSFORM)

transform: validate
	$(RUN) linkml-map map-data \
		-T $(TRANSFORM) \
		-s $(SOURCE_SCHEMA) \
		--target-schema $(TARGET_SCHEMA) \
		-o $(OUTPUT) \
		$(INPUT_DIR)
```

`make transform` then validates the data and spec before running the transformation. See the [Tutorial Notebook](examples/Tutorial.ipynb) for a deeper walk-through of the transformation language itself.

## Details

This repo contains both:

- A [data model](schema/) for a data model *transformation language*
- A reference Python implementation (ObjectTransformer)
- An experimental SQL compilation backend (SQLCompiler / DuckDBTransformer)

The transformation language is specified in terms of [LinkML](https://linkml.io) schemas.
It is intended to be a *polyglot* transformation language, used for
specifying how to map data models independent of underlying representation
(TSVs, JSON/YAML, RDF, SQL Database, ...). The same TransformationSpecification
can be interpreted in Python (full feature support) or compiled to SQL
(experimental, limited subset).

Use cases include:

- ETL and mapping from one data model to another
- Database migrations (one version of a schema to another)
- Creating "profiles"
- Specifying mappings between different serializations of a model (e.g. OO to Relational)
- Mapping between normalized/non-redundant forms and denormalized/query-optimized forms

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

## Data Model

The data model for transformations mirrors the data model for schemas:

- A top level [TransformationSpecification](schema/TransformationSpecification.md) class contains:
   - Zero or more [ClassDerivation](schema/ClassDerivation.md) objects, specifying how to map to a class, containing
       - Zero or more [SlotDerivation](schema/SlotDerivation.md) objects, specifying how to map to a slot
   - Zero or more [EnumDerivation](schema/EnumDerivation.md) objects, specifying how to map to an enum

See the [generated docs](schema/index.md)

## Conformance Suite

The Maps conformance suite contains a collection of tests for each feature of the language.

See:

* [Compliance Suite](specification/compliance.md)


## Running the code

The `linkml-map` CLI has the following subcommands:

- `map-data` — transform data from a source schema using a transformation specification
- `derive-schema` — derive a target schema from a source schema and a transformation specification
- `invert` — invert a transformation specification (when expressions are reversible)
- `compile` — compile a transformation specification to another representation
- `validate-spec` — structurally validate transformation specification files

Run any subcommand with `--help` for full options.

### map-data

Transforms (maps) data from a source schema to a target schema. This could range from a simple data dictionary mapping
through to a complex mapping.

```bash
cd tests/input/examples/personinfo_basic
linkml-map map-data --unrestricted-eval \
  -T transform/personinfo-to-agent.transform.yaml \
  -s source/personinfo.yaml \
  data/Container-001.yaml
```

#### Tabular Data Support (TSV/CSV)

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

#### Multi-Format Output

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
`.yaml`, `.yml`, `.tsv`, `.csv`). All outputs are written in a single streaming pass.

### derive-schema

Derives a target schema (the "profile") implied by the transformation specification.

```bash
cd tests/input/examples/personinfo_basic
linkml-map derive-schema -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml
```

### validate-spec

Structurally validates a transformation specification against source and target schemas. Reports unresolved class/slot references, deprecated fields, and other issues.

```bash
linkml-map validate-spec \
  --source-schema source/personinfo.yaml \
  --target-schema target/agent.yaml \
  transform/personinfo-to-agent.transform.yaml
```

Use `--strict` to treat warnings as errors. Supports validating multiple files or directories of specs in a single call.

### compile

Compiles a transformation specification to another representation.

```bash
linkml-map compile --target python -T transform.yaml -s source.yaml
linkml-map compile --target markdown -T transform.yaml -s source.yaml
```

Currently supported `--target` values are `python` (default) and `markdown`. A SQL compilation backend (`SQLCompiler` / `DuckDBTransformer`) exists for programmatic use but is not yet exposed through the `compile` subcommand.
