"""Validate transformation specification YAML files against the transformer model schema.

Uses the LinkML JSON Schema generator to produce a JSON Schema from
``transformer_model.yaml``, then validates data with the ``jsonschema`` library.

Includes a workaround for linkml/linkml#3366 (``add_lax_def`` crashes on schemas
with abstract classes that lack a ``required`` field in their JSON Schema
representation).

Example::

    >>> from linkml_map.validator import validate_spec_file
    >>> errors = validate_spec_file("tests/input/examples/flattening/transform/denormalize.transform.yaml")
    >>> errors
    []
"""

import json
import logging
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Union

import jsonschema
import yaml
from linkml.generators.jsonschemagen import JsonSchemaGenerator

from linkml_map.datamodel import TR_SCHEMA
from linkml_map.transformer.transformer import Transformer

logger = logging.getLogger(__name__)

# Abstract classes referenced in the generated JSON Schema but missing from
# $defs due to linkml/linkml#3366.
_ABSTRACT_CLASS_PATCHES = [
    "ElementDerivation",
    "ElementDerivation__identifier_optional",
]


@lru_cache(maxsize=1)
def _build_json_schema(schema_path: str | None = None) -> dict[str, Any]:
    """Generate and patch the JSON Schema for transformer model validation.

    The result is cached so repeated calls are cheap.

    :param schema_path: Path to the LinkML schema YAML.  Defaults to the
        bundled ``transformer_model.yaml``.
    :returns: A JSON Schema dict ready for ``jsonschema`` validation.
    """
    path = schema_path or str(TR_SCHEMA)
    gen = JsonSchemaGenerator(path)
    json_schema = json.loads(gen.serialize())

    # Patch: add stub definitions for abstract classes that the generator
    # references via $ref but omits from $defs (linkml/linkml#3366).
    defs = json_schema.setdefault("$defs", {})
    for name in _ABSTRACT_CLASS_PATCHES:
        if name not in defs:
            defs[name] = {"type": "string", "description": "Reference by name"}

    # The linkml JSON Schema generator sets additionalProperties: true at the
    # top level (the inlined tree_root class).  Override to false so that
    # unknown fields are rejected, matching the $defs version of the class.
    json_schema["additionalProperties"] = False

    return json_schema


def _coerce_yaml_types(obj: Any) -> Any:
    """Recursively convert YAML-parsed types that JSON Schema rejects.

    YAML auto-parses ``2025-08-14`` as :class:`datetime.date` and ``0.1`` as
    a float when the schema expects strings.  This coerces them so validation
    doesn't produce false positives on well-formed specs.
    """
    if isinstance(obj, dict):
        return {k: _coerce_yaml_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_coerce_yaml_types(item) for item in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, float):
        return str(obj)
    return obj


# Fields where YAML type coercion should be applied.  We only coerce at the
# top level to avoid mangling expression strings or numeric values deeper
# in the spec (e.g. value_mappings).
_COERCE_FIELDS = {"version", "publication_date"}


def normalize_spec_dict(obj: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw spec dict for validation.

    Applies the same full normalization pipeline that the transformer engine
    uses (compact-key expansion, dict→list conversion via ReferenceValidator,
    nested ObjectDerivation fixup), plus YAML type coercion for fields that
    are commonly mis-parsed.

    If normalization itself fails (e.g. due to malformed data), the original
    dict is returned with only YAML type coercion applied so that JSON Schema
    validation can still report structural errors.

    :param obj: Raw YAML-loaded dict.
    :returns: A new dict suitable for JSON Schema validation.
    """
    obj = dict(obj)
    try:
        Transformer._normalize_spec_dict(obj)
    except Exception:
        logger.debug("Normalization failed; falling back to raw dict", exc_info=True)
    for field in _COERCE_FIELDS:
        if field in obj:
            obj[field] = _coerce_yaml_types(obj[field])
    return obj


def validate_spec(
    data: dict[str, Any],
    *,
    schema_path: str | None = None,
) -> list[str]:
    """Validate a transformation specification dict against the schema.

    :param data: A raw YAML-loaded transformation specification dict.
    :param schema_path: Optional override for the LinkML schema path.
    :returns: A list of human-readable error messages (empty if valid).

    Example::

        >>> import yaml
        >>> from linkml_map.validator import validate_spec
        >>> with open("tests/input/examples/flattening/transform/denormalize.transform.yaml") as f:
        ...     data = yaml.safe_load(f)
        >>> validate_spec(data)
        []
    """
    json_schema = _build_json_schema(schema_path)
    normalized = normalize_spec_dict(data)
    validator = jsonschema.Draft202012Validator(json_schema)
    return [f"{e.json_path}: {e.message}" for e in sorted(validator.iter_errors(normalized), key=lambda e: e.json_path)]


def validate_spec_file(
    path: Union[str, Path],
    *,
    schema_path: str | None = None,
) -> list[str]:
    """Validate a transformation specification YAML file.

    :param path: Path to the YAML file.
    :param schema_path: Optional override for the LinkML schema path.
    :returns: A list of human-readable error messages (empty if valid).

    Example::

        >>> from linkml_map.validator import validate_spec_file
        >>> validate_spec_file("tests/input/examples/flattening/transform/denormalize.transform.yaml")
        []
    """
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return [f"Expected a YAML mapping at top level, got {type(data).__name__}"]
    return validate_spec(data, schema_path=schema_path)
