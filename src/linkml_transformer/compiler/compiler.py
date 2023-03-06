from abc import ABC
from dataclasses import dataclass

from linkml_runtime import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot

from linkml_transformer.datamodel.transformer_model import \
    TransformationSpecification


@dataclass
class Compiler(ABC):
    """
    Base class for all compiler.

    A compiler will compile a transformation specification into
    an alternative representation.

    An example compiler would be a R2RML compiler.
    """

    source_schemaview: SchemaView = None
    """A view over the schema describing the source."""

    @abstractmethod
    def compile(self, specification: TransformationSpecification) -> YAMLRoot:
        """
        Transform source object into an instance of the target class.

        :param specification:
        :return:
        """
        raise NotImplementedError
