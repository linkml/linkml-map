from abc import ABC
from dataclasses import dataclass
from typing import Iterator

from linkml_runtime import SchemaView

from linkml_transformer.datamodel.transformer_model import TransformationSpecification


@dataclass
class CompiledSpecification:
    serialization: str


@dataclass
class Compiler(ABC):
    """
    Base class for all compilers.

    A compiler will compile a transformation specification into
    an alternative representation.

    An example compiler would be a R2RML compiler.
    """

    source_schemaview: SchemaView = None
    """A view over the schema describing the source."""

    def compile(self, specification: TransformationSpecification) -> CompiledSpecification:
        """
        Transform source object into an instance of the target class.

        :param specification:
        :return:
        """
        s = ""
        for chunk in self._compile_iterator(specification):
            s += chunk
        return CompiledSpecification(serialization=s)

    def _compile_iterator(self, specification: TransformationSpecification) -> Iterator[str]:
        raise NotImplementedError
