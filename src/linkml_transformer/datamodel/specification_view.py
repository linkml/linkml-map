from dataclasses import dataclass
from typing import List

from linkml_transformer.datamodel.transformer_model import (
    ElementDerivation,
    TransformationSpecification,
)


@dataclass
class TransformerSpecificationView:
    specification: TransformationSpecification = None

    def derivations(self, derivation: ElementDerivation) -> List[ElementDerivation]:
        """Return all derivations of a given derivation"""
        closure = [derivation]
        return closure
