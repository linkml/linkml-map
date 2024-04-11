"""
Compilers are responsible for compiling a transformation specification into an alternative representation.

This is the opposite of an importer.

For example:

- LinkML-Transformer Specifications to R2RML
- LinkML-Transformer Specifications to awk scripts
- LinkML-Transformer Specifications to SQL
- LinkML-Transformer Specifications to Python (OO)
- LinkML-Transformer Specifications to Pandas
- LinkML-Transformer Specifications to Hamilton
"""

from abc import ABC
from dataclasses import dataclass, field
from types import ModuleType
from typing import Iterator, Optional

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.utils.compile_python import compile_python

from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.inference.schema_mapper import SchemaMapper


@dataclass
class CompiledSpecification:
    serialization: str = field(default="")

    _module: Optional[ModuleType] = None

    @property
    def module(self) -> ModuleType:
        if not self._module:
            self._module = compile_python(self.serialization)
        return self._module


@dataclass
class Compiler(ABC):
    """
    Base class for all compilers.

    A compiler will compile a transformation specification into
    an alternative representation.

    An example compiler would be a R2RML compiler.

    Note: Compilers and Importers will in general be implemented by providing
    mapping specifications
    """

    source_schemaview: SchemaView = None
    """A view over the schema describing the source."""

    source_python_module: str = None
    """The python module containing the source classes."""

    target_python_module: str = None
    """The python module containing the target classes."""

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        """
        Transform source object into an instance of the target class.

        :param specification:
        :return:
        """
        s = self._compile_header(specification)
        for chunk in self._compile_iterator(specification):
            s += chunk
        return CompiledSpecification(serialization=s)

    def _compile_header(self, specification: TransformationSpecification) -> str:
        return ""

    def _compile_iterator(self, specification: TransformationSpecification) -> Iterator[str]:
        raise NotImplementedError

    def derived_target_schemaview(self, specification: TransformationSpecification):
        """
        Returns a view over the target schema, including any derived classes.
        """
        mapper = SchemaMapper(source_schemaview=self.source_schemaview)
        return SchemaView(yaml_dumper.dumps(mapper.derive_schema(specification)))
