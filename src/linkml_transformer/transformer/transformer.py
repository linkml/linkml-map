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
    Base class for all transformers
    """
    source_schemaview: SchemaView = None
    target_schemaview: SchemaView = None
    target_module: ModuleType = None
    specification: TransformationSpecification = None

    def transform(self, obj: YAMLRoot, target_class: Type[YAMLRoot]) -> YAMLRoot:
        """
        Transform an object from source schema to an object conforming to target schema,
        following a specification

        :param obj:
        :param target_class:
        :return:
        """
        raise NotImplementedError

