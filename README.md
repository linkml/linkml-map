# linkml-transformer

THIS PACKAGE HAS BEEN RENAMED

It is now called linkml-map: https://pypi.org/project/linkml-map/

[![Pyversions](https://img.shields.io/pypi/pyversions/linkml-transformer.svg)](https://pypi.python.org/pypi/linkml-transformer)
![](https://github.com/linkml/linkml-transformer/workflows/Build/badge.svg)
[![PyPi](https://img.shields.io/pypi/v/linkml-transformer.svg)](https://pypi.python.org/pypi/linkml-transformer)
[![codecov](https://codecov.io/gh/linkml/linkml-transformer/branch/main/graph/badge.svg?token=WNQNG986UN)](https://codecov.io/gh/linkml/linkml-transformer)

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

For full documentation see:

- [linkml.io/linkml-transformer/](https://linkml.io/linkml-transformer/)

Status:

The transformation data model is not yet fully stable, and may be subject to change.
Not all parts of the model are implemented in the reference Python framework.

## Quickstart

* [Tutorial Notebook](src/docs/examples/Tutorial.ipynb)
* [Generated Docs](https://linkml.github.io/linkml-transformer/)
* [Compliance Suite](https://linkml.github.io/linkml-transformer/specification/compliance)

