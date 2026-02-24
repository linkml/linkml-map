from pathlib import Path
from typing import Union

import yaml

from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.transformer.transformer import Transformer


def load_specification(path: Union[Path, str]) -> TransformationSpecification:
    if isinstance(path, Path):
        path = str(path)
    with open(path) as f:
        obj = yaml.safe_load(f)
        Transformer._normalize_spec_dict(obj)
        return TransformationSpecification(**obj)
