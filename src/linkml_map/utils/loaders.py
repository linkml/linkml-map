from pathlib import Path
from typing import Any

import yaml

from linkml_map.datamodel.transformer_model import TransformationSpecification
from linkml_map.spec_normalizer import normalize_spec


def load_specification(spec: TransformationSpecification | dict[str, Any] | Path | str) -> TransformationSpecification:
    """
    Load a transformation specification from a YAML file, a dict, or an existing specification.

    A dict is normalized in place, as a file's contents are. An existing specification is returned as is.

    >>> spec = load_specification({"class_derivations": {"Agent": {"populated_from": "Person"}}})
    >>> spec.class_derivations[0].name
    'Agent'
    >>> load_specification(spec) is spec
    True
    """
    if isinstance(spec, TransformationSpecification):
        return spec
    if isinstance(spec, dict):
        normalize_spec(spec)
        return TransformationSpecification(**spec)
    with open(spec) as f:
        return load_specification(yaml.safe_load(f))
