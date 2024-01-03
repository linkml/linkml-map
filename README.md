# linkml-transformer

LinkML Transformer is a framework for specifying and executing mappings between data models.

Features:

- YAML-based lightweight syntax
- Python library for executing mappings on data files
- Ability to compile to other frameworks (forthcoming)
- Derivation of target (implicit) schemas, allowing easy customization of data models (*profiling*)
- Simple YAML dictionaries for simple mappings
- Automatic unit conversion
- Use of subset of Python to specify complex mappings
- Visualizations of mappings
- Mappings are reversible (provided all expressions used are reversible)

Status:

The transformation data model is not yet fully stable, and may be subject to change.
Not all parts of the model are implemented in the reference Python framework.

## Quickstart

* [Tutorial Notebook](notebooks/Tutorial.ipynb)
* [Generated Docs](https://linkml.github.io/linkml-transformer/)
* [Compliance Suite](https://linkml.github.io/linkml-transformer/specification/compliance)

## Basic idea

Given an object that conforms to a LinkML schema,e.g.:

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

Transform the data:

```yaml
name: Jane Doe
height_in_meters: 1.72
aliases: Janey|Janie
```

## Installation and usage

Installation and command line usage:

```bash
pip[x] install linkml-transformer
cd tests/input/examples/personinfo_basic
linkml-tr map-data \
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

- A data model for a data model *transformation language*
- A reference python implementation

The transformation language is specified in terms of LinkML schemas.
It is intended to be a *ployglot* transformation language, used for
specifying how to map data models independent of underlying representation
(TSVs, JSON/YAML, RDF, SQL Database, ...).

Use cases include:

- ETL and mapping from one data model to another
- Database migrations (one version of a schema to another)
- Creating "profiles"
- Specifying mappings between different serializations of a model (e.g. OO to Relational)
- Mapping between normalized/non-redundant forms and denormalized/query-optimized forms

## Tutorials

* [Tutorial Notebook](notebooks/Tutorial.ipynb) - for Python developers

## Data Model

The data model for transformations mirrors the data model for schemas:

- A top level `TransformationSpecification` class contains:
   - Zero or more `ClassDerivation` objects, specifying how to map to a class, containing:
       - Zero or more `SlotDerivation` objects, specifying how to map to a slot, containing:
   - Zero or more `EnumDerivation` objects, specifying how to map permissable values.

See the [generated docs](https://linkml.github.io/linkml-transformer/)

## Conformance Suite

The Transformers conformance suite contains a collection of tests for each feature of the language.

See:

* [Compliance Suite](https://linkml.github.io/linkml-transformer/specification/compliance)


## Running the code

```bash
linkml-tr --help
Usage: linkml-tr [OPTIONS] COMMAND [ARGS]...

  CLI for linkml-transformer.

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
linkml-tr map-data -T transform/personinfo-to-agent.transform.yaml -s source/personinfo.yaml  data/Container-001.yaml
```

### derive-schema

```
cd tests/input/examples/personinfo_basic
linkml-tr derive-schema -T transform/personinfo-to-agent.transform.yaml source/personinfo.yaml
```


## Examples

See the tests folder for most up-to-date examples

### Mapping between two similar data models

Given a *source* object

```yaml
persons:
  - id: P:001
    name: fred bloggs
    primary_email: fred.bloggs@example.com
    age_in_years: 33
    has_familial_relationships:
      - type: SIBLING_OF
        related_to: P:002
    current_address:
      street: 1 oak street
    aliases:
      - a
      - b
    has_medical_history:
      - diagnosis:
          id: C:001
          name: c1
      - diagnosis:
          id: C:002
  - id: P:002
    name: Alison Wu
    has_familial_relationships:
      - type: SIBLING_OF
        related_to: P:001
    has_medical_history:
      - diagnosis:
          id: C:001
          name: c1 (renamed)
organizations:
  - id: ROR:1
    name: Acme
```

and a corresponding schema, consider the case
of mapping to a largely isomorphic schema, with some minor differences:

- class names are changes (e.g Person to Agent)
- age is represented as a string, e.g. "33 years"
- some fields are denormalized

The mapping may look like:

```yaml
id: my-mappings
title: my mappings
prefixes:
  foo: foo
source_schema: s1
target_schema: s2
class_derivations:
  Container:
    populated_from: Container
    slot_derivations:
      agents:
        populated_from: persons
  Agent:
    populated_from: Person
    slot_derivations:
      
      ## implicitly same name in Agent
      id:

      label:
        populated_from: name

      age:
        expr: "str({age_in_years})+' years'"

      primary_email:

      gender:

      has_familial_relationships:
        populated_from: has_familial_relationships

  FamilialRelationship:
    populated_from: FamilialRelationship
    slot_derivations:
      type:
      related_to:
```

### Deriving Schemas

Formally a mapping consists of a source schema `S`, a target schema `T`, and a mapping `M`.

In practice, any of these can be *partially* specified and derived from the others.

For example:

- given `S`, and `T`, derive *isomorphic mappings* `M` based on shared URIs
- given `S and `M`, derive `T` by applying M to the schema

You can use the `derive-schema` command to derive a schema from a source schema and a mapping.
This can also be thought of as "profiling" a schema (in the FHIR sense). 

See [tests/test_mapper/test_schema_mapper.py](tests/test_schema_mapper/test_schema_mapper.py) for examples

### Measurements and units

```yaml
- id: P:001
  height:
    value: 172.0
    unit: cm
```

<==>

```yaml
- id: P:001
  height_in_cm: 172.0
```

<==>

```yaml
- id: P:001
  height: "172.0 cm"
```

## Not supported

- Aggregation

## Why another framework?

There are a number of excellent frameworks for performing mapping and data transformations.
The LinkML Transformer framework was born out of a need for a framework that:

- was not inherently tied to:
     - a particular serialization format (e.g. RDF, JSON, ...)
     - a particular programming language (e.g. Python, Java, ...)
     - a particular database system or database language (e.g. PostgreSQL or SQL or SPARQL)
     - not tied to a particular kind of transformation (e.g. ORM or Tables to RDF)
- was a natural fit for the LinkML data modeling framework
- was declarative and easy to perform machine reasoning over
- is simple for simple use cases

In its current state, this framework is less powerful and expressive than many other frameworks
or methodologies for performing transformations. If you need to perform complex data transformations,
you might be better off using an expressive query language like SPARQL or SQL, or even just coding
transformations directly in a programming language or library like Python or Pandas (but note that
even for the coding use case, the LinkML Transformer framework can be useful as a standard way
of *documenting* transformations).

Currently the main use case for this framework is *mostly isomorphic* transformations, with lightweight
manipulations. These lend themselves well to a declarative framework. Uses cases that are a particularly good fit
involve mapping between data-dictionary like standards, with large numbers of metadata elements, where these
elements can often be mapped one-to-one, or with simple manipulations (e.g. unit conversions).

The origins lie partly in the SSSOM standard, which is intended as an ultra-simple way of specifying
precise mappings between *entities* (e.g. schema.org Person is the same as DBPedia person). We observed
that many people wanted to extend the language to perform more complex mappings. To address this, we
help a workshop at the Biocuration conference in Padua, Italy in 2022.

- [SSSOM paper](https://academic.oup.com/database/article/doi/10.1093/database/baac035/6591806)
- [SSSOM Update 2023](https://ceur-ws.org/Vol-3591/om2023_STpaper3.pdf)
- [SSSOM Complex Mappings Workshop 2023](https://www.youtube.com/playlist?list=PLqu_J7ADQtKyX55F7RqZtaSS7TwGd3MoR)
- [Mapping Data Structures: Challenges and Approaches](https://doi.org/10.5281/zenodo.10343505)
