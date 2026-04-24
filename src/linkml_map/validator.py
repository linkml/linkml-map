"""Validate transformation specification YAML files.

Provides two layers of validation:

1. **Structural** — validates that the spec YAML conforms to the
   ``transformer_model.yaml`` JSON Schema (correct keys, types, nesting).
2. **Semantic** — cross-references the spec against source and/or target
   LinkML schemas to check that class names, slot names, ``populated_from``
   references, and expression slot references actually resolve.

Example::

    >>> from linkml_map.validator import validate_spec_file
    >>> msgs = validate_spec_file("tests/input/examples/flattening/transform/denormalize.transform.yaml")
    >>> msgs
    []
"""

import ast
import concurrent.futures
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import jsonschema
import yaml
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime import SchemaView

from linkml_map.datamodel import TR_SCHEMA
from linkml_map.transformer.transformer import Transformer
from linkml_map.utils.eval_utils import FUNCTIONS

logger = logging.getLogger(__name__)

# Abstract classes referenced in the generated JSON Schema but missing from
# $defs due to linkml/linkml#3366.
_ABSTRACT_CLASS_PATCHES = [
    "ElementDerivation",
    "ElementDerivation__identifier_optional",
]

# Names that should never be treated as slot references in expressions.
_EXPR_SAFE_NAMES = frozenset(
    {
        # Python builtins / keywords used as values
        "True",
        "False",
        "None",
        # LinkML expression language builtins
        "NULL",
        "target",
        "src",
        # All registered evaluator functions
        *FUNCTIONS.keys(),
    }
)


@dataclass
class ValidationMessage:
    """A single validation finding with severity and location context."""

    severity: Literal["error", "warning"]
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: [{self.severity}] {self.message}"


# ---------------------------------------------------------------------------
# JSON Schema (structural) helpers
# ---------------------------------------------------------------------------


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
    if isinstance(obj, date | datetime):
        return obj.isoformat()
    if isinstance(obj, int | float):
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


def _validate_structural(
    data: dict[str, Any],
    *,
    schema_path: str | None = None,
) -> list[ValidationMessage]:
    """Run JSON Schema structural validation.

    :param data: A **normalized** spec dict.
    :param schema_path: Optional override for the LinkML schema path.
    :returns: A list of structural validation errors.
    """
    json_schema = _build_json_schema(schema_path)
    validator = jsonschema.Draft202012Validator(json_schema)
    return [
        ValidationMessage(severity="error", path=e.json_path, message=e.message)
        for e in sorted(validator.iter_errors(data), key=lambda e: e.json_path)
    ]


# ---------------------------------------------------------------------------
# Expression slot reference extraction
# ---------------------------------------------------------------------------


def extract_expr_slot_references(expr: str) -> set[str]:
    """Extract candidate slot name references from a LinkML expression.

    Uses :mod:`ast` to parse the expression and collect:

    - ``ast.Name`` nodes (covers both bare ``x`` and ``{x}`` syntax, since
      ``{x}`` is parsed as ``ast.Set({ast.Name('x')})``)
    - ``ast.Attribute`` nodes where the value is ``ast.Name('src')``
      (covers ``src.slot_name`` references in multi-line expressions)

    Known-safe names (Python builtins, evaluator functions, ``NULL``,
    ``target``, ``src``) are filtered out, as are locally bound names
    (assignment targets, comprehension variables).

    :param expr: A LinkML expression string.
    :returns: A set of candidate slot name strings.

    Example::

        >>> sorted(extract_expr_slot_references("str({age_in_years}) + ' years'"))
        ['age_in_years']
        >>> sorted(extract_expr_slot_references("subject.id"))
        ['subject']
        >>> sorted(extract_expr_slot_references("case((x == '1', 'YES'), (True, 'NO'))"))
        ['x']
        >>> extract_expr_slot_references("'hello'")
        set()
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        try:
            tree = ast.parse(expr, mode="exec")
        except SyntaxError:
            return set()

    names: set[str] = set()
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                bound.add(node.id)
            else:
                names.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "src":
            names.add(node.attr)
        elif isinstance(node, ast.comprehension) and isinstance(node.target, ast.Name):
            bound.add(node.target.id)

    return names - _EXPR_SAFE_NAMES - bound


# ---------------------------------------------------------------------------
# Semantic validation
# ---------------------------------------------------------------------------


# Timeout in seconds for loading schemas from URLs or remote identifiers.
_SCHEMA_LOAD_TIMEOUT = 10


def _load_schemaview_with_timeout(path: str, timeout: int = _SCHEMA_LOAD_TIMEOUT) -> SchemaView:
    """Load a SchemaView with a timeout to avoid hanging on unreachable URLs.

    :param path: Schema path, URL, or identifier.
    :param timeout: Maximum seconds to wait.
    :returns: A loaded :class:`SchemaView`.
    :raises TimeoutError: If loading exceeds the timeout.
    :raises Exception: Any exception raised by :class:`SchemaView`.
    """
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(SchemaView, path)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        msg = f"Timed out loading schema '{path}' after {timeout}s"
        raise TimeoutError(msg) from None
    finally:
        executor.shutdown(wait=False)


def _resolve_schema_path(
    spec_value: str | None,
    explicit: str | Path | None,
    base_path: Path | None,
) -> tuple[str | None, bool]:
    """Resolve a schema path from explicit argument or spec field.

    :param spec_value: The ``source_schema`` or ``target_schema`` value from the spec.
    :param explicit: An explicitly provided schema path (overrides spec_value).
    :param base_path: Directory to resolve relative paths against (typically
        the directory containing the spec file).
    :returns: A tuple of (resolved path string or ``None``, whether it was
        explicitly provided by the user).
    """
    if explicit is not None:
        return str(explicit), True
    if spec_value is None:
        return None, False
    # Try relative to spec file directory
    if base_path is not None:
        candidate = base_path / spec_value
        if candidate.exists():
            return str(candidate), False
    # Try as-is (absolute path)
    if Path(spec_value).exists():
        return spec_value, False
    # URLs: let SchemaView attempt resolution with a timeout
    if "://" in spec_value:
        return spec_value, False
    return None, False


def _iter_derivation_dicts(raw: Any) -> list[dict[str, Any]]:
    """Normalize a derivations section (dict or list) to a list of dicts.

    After ``normalize_spec_dict``, derivation sections may be either a list of
    dicts (with ``name`` keys) or a dict keyed by name.  This helper
    normalizes to a consistent list-of-dicts form for iteration.
    """
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        result: list[dict[str, Any]] = []
        for name, body in raw.items():
            d = dict(body) if isinstance(body, dict) else {}
            d.setdefault("name", name)
            result.append(d)
        return result
    return []


def validate_spec_semantics(
    data: dict[str, Any],
    *,
    source_schema: str | Path | None = None,
    target_schema: str | Path | None = None,
    strict: bool = False,
    spec_base_path: Path | None = None,
) -> list[ValidationMessage]:
    """Validate spec references against source and/or target schemas.

    Checks that class names, slot names, ``populated_from`` references, and
    expression slot references resolve against the provided schemas.

    :param data: A **normalized** spec dict.
    :param source_schema: Path to the source LinkML schema.
    :param target_schema: Path to the target LinkML schema.
    :param strict: If ``True``, unresolved expression slot references are
        errors instead of warnings.
    :param spec_base_path: Directory for resolving relative schema paths
        found in the spec's ``source_schema``/``target_schema`` fields.
    :returns: A list of validation messages.
    """
    messages: list[ValidationMessage] = []

    # Resolve schemas (explicit args override spec fields)
    source_path, source_explicit = _resolve_schema_path(data.get("source_schema"), source_schema, spec_base_path)
    target_path, target_explicit = _resolve_schema_path(data.get("target_schema"), target_schema, spec_base_path)

    source_sv: SchemaView | None = None
    target_sv: SchemaView | None = None

    if source_path:
        try:
            source_sv = _load_schemaview_with_timeout(source_path)
        except Exception as exc:
            messages.append(
                ValidationMessage(
                    severity="error" if source_explicit else "warning",
                    path="source_schema",
                    message=f"Could not load source schema '{source_path}': {exc}",
                )
            )

    if target_path:
        try:
            target_sv = _load_schemaview_with_timeout(target_path)
        except Exception as exc:
            messages.append(
                ValidationMessage(
                    severity="error" if target_explicit else "warning",
                    path="target_schema",
                    message=f"Could not load target schema '{target_path}': {exc}",
                )
            )

    if source_sv is None and target_sv is None:
        return messages

    # Validate class_derivations
    for cd in _iter_derivation_dicts(data.get("class_derivations", [])):
        _validate_class_derivation(cd, source_sv, target_sv, strict, messages)

    # Validate enum_derivations
    for ed in _iter_derivation_dicts(data.get("enum_derivations", [])):
        _validate_enum_derivation(ed, source_sv, target_sv, messages)

    return messages


def _validate_class_derivation(
    cd: dict[str, Any],
    source_sv: SchemaView | None,
    target_sv: SchemaView | None,
    strict: bool,
    messages: list[ValidationMessage],
) -> None:
    """Validate a single class derivation against schemas."""
    cd_name = cd.get("name", "?")
    cd_path = f"class_derivations[{cd_name}]"

    # Target: class name should exist
    target_class_slots: set[str] | None = None
    if target_sv is not None:
        target_classes = set(target_sv.all_classes())
        if cd_name not in target_classes:
            messages.append(
                ValidationMessage(
                    severity="error",
                    path=cd_path,
                    message=f"Target class '{cd_name}' not found in target schema",
                )
            )
        else:
            target_class_slots = {s.name for s in target_sv.class_induced_slots(cd_name)}

    # Source: populated_from class should exist
    source_class = cd.get("populated_from")
    source_class_slots: set[str] | None = None
    if source_sv is not None and source_class is not None:
        source_classes = set(source_sv.all_classes())
        if source_class not in source_classes:
            messages.append(
                ValidationMessage(
                    severity="error",
                    path=cd_path,
                    message=f"Source class '{source_class}' (populated_from) not found in source schema",
                )
            )
        else:
            source_class_slots = {s.name for s in source_sv.class_induced_slots(source_class)}

    # If source_sv provided but no populated_from, try identity (class name = source class)
    if source_sv is not None and source_class is None and source_class_slots is None:
        if cd_name in source_sv.all_classes():
            source_class_slots = {s.name for s in source_sv.class_induced_slots(cd_name)}

    # Validate slot_derivations (may be list or dict after normalization)
    slot_derivation_dicts = _iter_derivation_dicts(cd.get("slot_derivations", []))

    for sd in slot_derivation_dicts:
        _validate_slot_derivation(
            sd,
            cd_name,
            cd_path,
            source_class_slots,
            target_class_slots,
            strict,
            messages,
        )

    # Warning: target class has required slots with no derivation
    if target_sv is not None and target_class_slots is not None:
        derived_slot_names = {sd.get("name") for sd in slot_derivation_dicts if "name" in sd}
        for slot in target_sv.class_induced_slots(cd_name):
            if slot.required and slot.name not in derived_slot_names:
                messages.append(
                    ValidationMessage(
                        severity="warning",
                        path=cd_path,
                        message=f"Required target slot '{slot.name}' has no derivation",
                    )
                )


def _validate_slot_derivation(
    sd: dict[str, Any],
    parent_class_name: str,
    parent_path: str,
    source_class_slots: set[str] | None,
    target_class_slots: set[str] | None,
    strict: bool,
    messages: list[ValidationMessage],
) -> None:
    """Validate a single slot derivation against schemas."""
    sd_name = sd.get("name", "?")
    sd_path = f"{parent_path}.slot_derivations[{sd_name}]"

    # Target: slot name should be valid on the target class
    if target_class_slots is not None and sd_name not in target_class_slots:
        messages.append(
            ValidationMessage(
                severity="error",
                path=sd_path,
                message=f"Slot '{sd_name}' not found on target class '{parent_class_name}'",
            )
        )

    # Source: populated_from slot should be valid on the source class
    populated_from = sd.get("populated_from")
    if source_class_slots is not None and populated_from is not None:
        if populated_from not in source_class_slots:
            messages.append(
                ValidationMessage(
                    severity="error",
                    path=sd_path,
                    message=f"Source slot '{populated_from}' (populated_from) not found on source class",
                )
            )

    # Expression slot references
    expr = sd.get("expr")
    if expr is not None and source_class_slots is not None:
        refs = extract_expr_slot_references(expr)
        for ref in sorted(refs):
            if ref not in source_class_slots:
                messages.append(
                    ValidationMessage(
                        severity="error" if strict else "warning",
                        path=sd_path,
                        message=f"Expression references '{ref}' which is not a slot on the source class",
                    )
                )


def _validate_enum_derivation(
    ed: dict[str, Any],
    source_sv: SchemaView | None,
    target_sv: SchemaView | None,
    messages: list[ValidationMessage],
) -> None:
    """Validate a single enum derivation against schemas."""
    ed_name = ed.get("name", "?")
    ed_path = f"enum_derivations[{ed_name}]"

    if target_sv is not None:
        target_enums = set(target_sv.all_enums())
        if ed_name not in target_enums:
            messages.append(
                ValidationMessage(
                    severity="error",
                    path=ed_path,
                    message=f"Target enum '{ed_name}' not found in target schema",
                )
            )

    populated_from = ed.get("populated_from")
    if source_sv is not None and populated_from is not None:
        source_enums = set(source_sv.all_enums())
        if populated_from not in source_enums:
            messages.append(
                ValidationMessage(
                    severity="error",
                    path=ed_path,
                    message=f"Source enum '{populated_from}' (populated_from) not found in source schema",
                )
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_spec(
    data: dict[str, Any],
    *,
    schema_path: str | None = None,
    source_schema: str | Path | None = None,
    target_schema: str | Path | None = None,
    strict: bool = False,
    spec_base_path: Path | None = None,
) -> list[ValidationMessage]:
    """Validate a transformation specification dict.

    Runs structural validation (JSON Schema) first, then semantic validation
    (cross-referencing against source/target schemas) if schemas are provided
    or auto-detectable from the spec's ``source_schema``/``target_schema`` fields.

    :param data: A raw YAML-loaded transformation specification dict.
    :param schema_path: Optional override for the LinkML schema path.
    :param source_schema: Path to the source LinkML schema.
    :param target_schema: Path to the target LinkML schema.
    :param strict: If ``True``, unresolved expression slot references are
        errors instead of warnings.
    :param spec_base_path: Directory for resolving relative schema paths.
    :returns: A list of :class:`ValidationMessage` objects (empty if valid).

    Example::

        >>> import yaml
        >>> from linkml_map.validator import validate_spec
        >>> with open("tests/input/examples/flattening/transform/denormalize.transform.yaml") as f:
        ...     data = yaml.safe_load(f)
        >>> validate_spec(data)
        []
    """
    normalized = normalize_spec_dict(data)
    messages = _validate_structural(normalized, schema_path=schema_path)
    if not messages:
        messages.extend(
            validate_spec_semantics(
                normalized,
                source_schema=source_schema,
                target_schema=target_schema,
                strict=strict,
                spec_base_path=spec_base_path,
            )
        )
    return messages


def validate_spec_file(
    path: str | Path,
    *,
    schema_path: str | None = None,
    source_schema: str | Path | None = None,
    target_schema: str | Path | None = None,
    strict: bool = False,
) -> list[ValidationMessage]:
    """Validate a transformation specification YAML file.

    :param path: Path to the YAML file.
    :param schema_path: Optional override for the LinkML schema path.
    :param source_schema: Path to the source LinkML schema.
    :param target_schema: Path to the target LinkML schema.
    :param strict: If ``True``, unresolved expression slot references are
        errors instead of warnings.
    :returns: A list of :class:`ValidationMessage` objects (empty if valid).

    Example::

        >>> from linkml_map.validator import validate_spec_file
        >>> validate_spec_file("tests/input/examples/flattening/transform/denormalize.transform.yaml")
        []
    """
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return [
            ValidationMessage(
                severity="error",
                path="$",
                message=f"Expected a YAML mapping at top level, got {type(data).__name__}",
            )
        ]
    return validate_spec(
        data,
        schema_path=schema_path,
        source_schema=source_schema,
        target_schema=target_schema,
        strict=strict,
        spec_base_path=path.parent,
    )
