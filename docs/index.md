# LinkML-Map

LinkML Map is a framework for specifying and executing mappings between data models.

Features:

- YAML-based lightweight syntax
- Python library for executing mappings on data files
- Ability to compile to other frameworks (SQL/DuckDB)
- Derivation of target (implicit) schemas, allowing easy customization of data models (*profiling*)
- Simple YAML dictionaries for simple mappings
- Automatic unit conversion
- Use of subset of Python to specify complex mappings
- Visualizations of mappings
- Mappings are reversible (provided all expressions used are reversible)
- Compatibility with SSSOM

This documentation are available at:

- [linkml.io/linkml-map/](https://linkml.io/linkml-map/)

Status:

The transformation data model is not yet fully stable, and may be subject to change.
Not all parts of the model are implemented in the reference Python framework.

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

Transform the data:

```bash
linkml-map map-data -T tr.yaml -s schema.yaml my-data.yaml
```

Giving:

```yaml
name: Jane Doe
height_in_meters: 1.72
aliases: Janey|Janie
```

## Installation and usage

Installation and command line usage:

```bash
pip[x] install linkml-map
cd tests/input/examples/personinfo_basic
linkml-map map-data \
  -T transform/personinfo-to-agent.transform.yaml \
  -s source/personinfo.yaml \
   data/Container-001.yaml \
   -o output/Translated-001.yaml
```

The command line has subcommands for:

- `map-data` - map data from a source schema to a target schema
- `derive-schema` - derive a target schema from a source schema and a mapping
- `invert` - reverses a mapping
- `compile` - compiles a mapping to another framework
    - `markdown` - for generating static sites
    - `graphviz` - for generating visualizations
    - `python` - (partial)
    - forthcoming: `r2rml`, ...
 
## Details

This repo contains both:

- A [data model](schema/) for a data model *transformation language*
- A reference python implementation

The transformation language is specified in terms of [LinkML](https://linkml.io) schemas.
It is intended to be a *ployglot* transformation language, used for
specifying how to map data models independent of underlying representation
(TSVs, JSON/YAML, RDF, SQL Database, ...).

Use cases include:

- ETL and mapping from one data model to another
- Database migrations (one version of a schema to another)
- Creating "profiles"
- Specifying mappings between different serializations of a model (e.g. OO to Relational)
- Mapping between normalized/non-redundant forms and denormalized/query-optimized forms


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

```bash
linkml-map --help
Usage: linkml-map [OPTIONS] COMMAND [ARGS]...

  CLI for linkml-map.

Options:
  -v, --verbose
  -q, --quiet TEXT
  --help            Show this message and exit.

Commands:
  derive-schema  Derive a schema from a source schema and a mapping.
  map-data       Map data in a source schema using a transformation.
```

### map-data

Transforms (maps) data from a source schema to a target schema. This could range from a simple data dictionary mapping
through to a complex mappings.

```
cd tests/input/examples/personinfo_basic
linkml-map map-data -T transform/personinfo-to-agent.transform.yaml -s source/personinfo.yaml  data/Container-001.yaml
```

### derive-schema

```
cd tests/input/examples/personinfo_basic
linkml-map derive-schema -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml
```

