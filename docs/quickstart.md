# Quick Start

## Install

```bash
pip install linkml-map
```

Or with `uv` for project-managed environments:

```bash
uv add linkml-map
```

Verify the install:

```bash
linkml-map --help
```

When using `uv`, prefix CLI invocations with `uv run` to use the project environment (e.g. `uv run linkml-map --help`).

## Run the included example

The repository includes a `personinfo_basic` example that transforms `Person` records into `Agent` records. Clone the repo to get the example files:

```bash
git clone https://github.com/linkml/linkml-map.git
cd linkml-map/tests/input/examples/personinfo_basic
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
derivations can target the same class (their slot derivations are merged).

Run the transformation:

```bash
linkml-map map-data -T tr.yaml -s schema.yaml my-data.yaml
```

Giving:

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

Validate the spec first, then run the transformation:

```bash
mkdir -p output

linkml-map validate-spec \
  --source-schema source.yaml \
  --target-schema target.yaml \
  transform.yaml

linkml-map map-data \
  -T transform.yaml \
  -s source.yaml \
  --target-schema target.yaml \
  -o output/result.yaml \
  data.yaml
```

For large datasets, add `--chunk-size N` for streaming output. See the [Command-Line Reference](cli.md) for the full set of CLI options per subcommand (including directory-mode input, tabular formats, and multi-format output), and the [Tutorial Notebook](examples/Tutorial.ipynb) for a deeper walk-through of the transformation language itself.
