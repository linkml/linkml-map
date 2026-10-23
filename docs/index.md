# LinkML-Map

LinkML Map is a framework for specifying and executing declarative mappings between data models.

The core of LinkML Map is the **TransformationSpecification** — a YAML-based language for describing
how to map one data model to another. This specification is independent of how the transformation
is executed or what format the data lives in.

Features:

- YAML-based lightweight transformation syntax
- A CLI and Python library for executing mappings on data files
- Validation of a specification against its source and target schemas before it runs (`validate-spec`)
- Output typed to the target schema, when one is given: values are coerced to the target slot's range and enum values resolved to permissible values
- Streaming support for large tabular datasets (TSV/CSV), with joins across tables
- Text (YAML, JSON, JSONL, TSV, CSV) and columnar (Parquet, DuckDB) output
- Derivation of target (implicit) schemas, allowing easy customization of data models (*profiling*)
- Simple YAML dictionaries for simple mappings
- Automatic unit conversion
- Use of subset of Python to specify complex mappings
- Visualizations of mappings
- Inversion of mappings built from renames, unit conversions and stringification (expressions can't be inverted)

## Architecture

The TransformationSpecification acts as a declarative intermediate representation that can be
interpreted by different execution backends:

- **ObjectTransformer** (Python) — interprets the spec row-by-row, supports the full feature set
  including Python expressions, unit conversion, and cross-class lookups.
- **SQLCompiler / DuckDBTransformer** (SQL) — an **experimental stub** that handles only plain
  `populated_from` renames. Any other slot derivation compiles to SQL that refers to a column
  that doesn't exist. Use the ObjectTransformer.

Transformed data serializes to text (YAML, JSON, JSONL, TSV, CSV) or to a columnar
artifact (Parquet, DuckDB). The columnar formats preserve nested structure that the
flat text formats cannot: a nested object becomes a `STRUCT` column rather than being
flattened away. See [Columnar Output](cli.md#columnar-output).

This documentation is available at:

- [linkml.io/linkml-map/](https://linkml.io/linkml-map/)

Status:

The transformation data model is not yet fully stable, and may be subject to change.
Not all parts of the model are implemented in the reference Python framework.

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
