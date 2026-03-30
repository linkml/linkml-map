# linkml-map

[![Pyversions](https://img.shields.io/pypi/pyversions/linkml-map.svg)](https://pypi.python.org/pypi/linkml-map)
![](https://github.com/linkml/linkml-map/workflows/Build/badge.svg)
[![PyPi](https://img.shields.io/pypi/v/linkml-map.svg)](https://pypi.python.org/pypi/linkml-map)
[![codecov](https://codecov.io/gh/linkml/linkml-map/branch/main/graph/badge.svg?token=WNQNG986UN)](https://codecov.io/gh/linkml/linkml-map)

LinkML Map is a framework for specifying and executing declarative mappings between data models.
At its core is the **TransformationSpecification** — a YAML-based language for describing how to
map one data model to another, independent of serialization format or execution engine.

Features:

- YAML-based lightweight transformation syntax
- Python library for executing mappings on data files
- **Tabular data support (TSV/CSV) with streaming for large datasets**
- Experimental SQL compilation backend (DuckDB) for set-based transforms
- Derivation of target (implicit) schemas, allowing easy customization of data models (*profiling*)
- Simple YAML dictionaries for simple mappings
- Automatic unit conversion
- Use of subset of Python to specify complex mappings
- Visualizations of mappings
- Mappings are reversible (provided all expressions used are reversible)
- Multiple output formats (YAML, JSON, JSONL, TSV, CSV)

For full documentation see:

- [linkml.io/linkml-map/](https://linkml.io/linkml-map/)

Status:

The transformation data model is not yet fully stable, and may be subject to change.
Not all parts of the model are implemented in the reference Python framework.

## Quickstart

* [Tutorial Notebook](docs/examples/Tutorial.ipynb)
* [Generated Docs](https://linkml.github.io/linkml-map/)
* [Compliance Suite](https://linkml.github.io/linkml-map/specification/compliance)
* [API Docs](https://linkml.github.io/linkml-map/api/)
