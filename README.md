# linkml-transformer

__Status__: pre-alpha code

See [these slides](https://docs.google.com/presentation/d/1ctgT1IfwPjnFQO2Q0sYlM8qk0wiB2_32JyeKyN4Uf8k/edit)

This repo contains both:

- A data model for a model *transformation* language
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

## Data Model

See [generated docs](https://linkml.github.io/linkml-transformer/)

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

See the tests folder for most up to date examples

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

Formally a mapping consists of a source schema S, a target schema T, and a mapping M.

In practice, any of these can be *partially* specified and derived from the others.

For example:

- given S, and T, derive isomorphic mappings based on shared URIs
- given S and M, derive T by applying M to the schema

See [tests/test_mapper/test_schema_mapper.py](tests/test_mapper/test_schema_mapper.py) for examples

### Measurements TODO

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


