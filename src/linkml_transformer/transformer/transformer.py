from abc import ABC
from dataclasses import dataclass
from types import ModuleType
from typing import Type

from linkml_runtime import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot
from linkml_transformer.datamodel.transformer_model import TransformationSpecification


@dataclass
class Transformer(ABC):
    """
    Base class for all transformers.

    A transformer will generate an instance of a target class from
    an instance of a source class, making use of a specification.

    This is an abstract class. Different implementations will
    subclass this
    """
    source_schemaview: SchemaView = None
    """A view over the schema describing the input/source object."""

    target_schemaview: SchemaView = None
    """A view over the schema describing the output/target object."""

    target_module: ModuleType = None
    """The python module which the target object should conform to."""

    specification: TransformationSpecification = None
    """A specification of how to generate target objects from source objects."""

    def transform(self, obj: YAMLRoot, target_class: Type[YAMLRoot]) -> YAMLRoot:
        """
        Transform source object into an instance of the target class.

        :param obj:
        :param target_class:
        :return:
        """
        raise NotImplementedError

