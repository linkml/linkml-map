from pathlib import Path
from typing import Union

import yaml
from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview

from linkml_map.datamodel.transformer_model import TransformationSpecification


def load_specification(path: Union[Path, str]) -> TransformationSpecification:
    if isinstance(path, Path):
        path = str(path)
    with open(path) as f:
        obj = yaml.safe_load(f)
        # necessary to expand first
        normalizer = ReferenceValidator(
            package_schemaview("linkml_map.datamodel.transformer_model")
        )
        normalizer.expand_all = True
        obj = normalizer.normalize(obj)
        return TransformationSpecification(**obj)
