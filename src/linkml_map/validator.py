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
    """A single validation finding with severity and location context.

    ``category`` is an optional tag that downstream consumers can use to
    group or filter messages. The validator currently emits ``"deprecated"``
    for warnings about deprecated field usage; other categories may be
    added in the future.
    """

    severity: Literal["error", "warning"]
    path: str
    message: str
    category: str | None = None

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
    nested ObjectDerivation fixup, deprecated-field migration), plus YAML
    type coercion for fields that are commonly mis-parsed.

    If normalization itself fails (e.g. due to malformed data), the original
    dict is returned with only YAML type coercion applied so that JSON Schema
    validation can still report structural errors.

    Use :func:`_normalize_and_collect_messages` instead when you also need
    the pre-normalize scan's findings (deprecation warnings, conflict errors).

    :param obj: Raw YAML-loaded dict.
    :returns: A new dict suitable for JSON Schema validation.
    """
    obj, _ = _normalize_and_collect_messages(obj)
    return obj


def _normalize_and_collect_messages(
    obj: dict[str, Any],
) -> tuple[dict[str, Any], list[ValidationMessage]]:
    """Normalize and return both the dict and the pre-normalize scan messages.

    Internal helper used by :func:`validate_spec`. Calls the transformer's
    normalization in silent mode so scan findings are returned as
    ``ValidationMessage`` records rather than emitted as Python warnings or
    raised as ``SpecificationError``.
    """
    obj = dict(obj)
    messages: list[ValidationMessage] = []
    try:
        messages = Transformer._normalize_spec_dict(obj, silent=True) or []
    except Exception:
        logger.debug("Normalization failed; falling back to raw dict", exc_info=True)
    for field in _COERCE_FIELDS:
        if field in obj:
            obj[field] = _coerce_yaml_types(obj[field])
    return obj, messages


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
    spec_value: dict | None,
    explicit: str | Path | None,
    base_path: Path | None,
) -> tuple[str | None, bool]:
    """Resolve a schema path from explicit argument or spec field.

    Auto-detection reads ``source_file`` (preferred) or ``name`` from the
    ``SchemaReference`` and supports **local file paths** (relative to the
    spec file or absolute) and **URLs** (any value containing ``://``).
    Identifier-style values (e.g. ``name: biolink``) are *not* auto-resolved
    — pass ``--source-schema`` / ``--target-schema`` explicitly to point at
    a real file or URL for those cases. Skipping silently here prevents typos
    from triggering surprise network requests during validation.

    :param spec_value: The ``source_schema`` or ``target_schema`` value from
        the normalized spec — a ``SchemaReference`` dict.
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
    locator = spec_value.get("source_file") or spec_value.get("name")
    if locator is None:
        return None, False
    # Try relative to spec file directory
    if base_path is not None:
        candidate = base_path / locator
        if candidate.exists():
            return str(candidate), False
    # Try as-is (absolute path)
    if Path(locator).exists():
        return locator, False
    # URLs: let SchemaView attempt resolution with a timeout
    if "://" in locator:
        return locator, False
    # Identifier-style values (no path, no URL): skip auto-detection.
    logger.debug(
        "Schema value %r is neither a resolvable path nor a URL; skipping auto-detection. "
        "Pass --source-schema / --target-schema to validate against this schema.",
        locator,
    )
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


def check_deprecated_fields(data: dict[str, Any]) -> list[ValidationMessage]:
    """Scan a spec dict for deprecated-field usage and ambiguous combinations.

    Runs **pre-migration** — i.e., on a structurally-normalized dict whose
    deprecated fields are still as the user wrote them. ``Transformer._normalize_spec_dict``
    calls this between structural normalization and field migration, so all
    deprecations are detectable here regardless of whether the migration step
    later removes them.

    Flags:

    * ``sources`` on ``ClassDerivation`` / ``SlotDerivation`` /
      ``EnumDerivation`` / ``PermissibleValueDerivation`` — replaced by
      ``populated_from``. Severity: warning, category: deprecated.
    * ``derived_from`` on ``SlotDerivation`` — ignored by the runtime
      and removable. Severity: warning, category: deprecated.
    * ``object_derivations`` on ``SlotDerivation`` — flattened into
      ``class_derivations`` at load time. Severity: warning, category:
      deprecated.
    * ``populated_from`` **and** ``sources`` both set on the same
      ``PermissibleValueDerivation`` — ambiguous, the user almost
      certainly didn't mean both. Severity: error.
    * ``object_derivations`` **and** ``class_derivations`` both set on
      the same ``SlotDerivation`` — ambiguous. Severity: error.

    ``sources`` deprecation findings are collapsed to one message per
    (deprecation, derivation type) pair to keep output readable on
    large specs; per-entry messages are emitted for the other categories.

    :param data: A structurally-normalized spec dict (post
        ``normalize_spec_dict``, pre field migration).
    :returns: A list of validation messages — warnings for deprecations,
        errors for ambiguous combinations.
    """
    messages: list[ValidationMessage] = []
    sources_counts: dict[str, list[str]] = {
        "ClassDerivation": [],
        "SlotDerivation": [],
        "EnumDerivation": [],
        "PermissibleValueDerivation": [],
    }
    derived_from_names: list[str] = []
    object_derivation_names: list[str] = []

    for cd in _iter_derivation_dicts(data.get("class_derivations")):
        cd_name = cd.get("name", "<unnamed>")
        if cd.get("sources"):
            sources_counts["ClassDerivation"].append(cd_name)
        for sd in _iter_derivation_dicts(cd.get("slot_derivations")):
            sd_name = sd.get("name", "<unnamed>")
            if sd.get("sources"):
                sources_counts["SlotDerivation"].append(sd_name)
            if sd.get("derived_from"):
                derived_from_names.append(sd_name)
            if sd.get("object_derivations"):
                object_derivation_names.append(sd_name)
                if sd.get("class_derivations"):
                    messages.append(
                        ValidationMessage(
                            severity="error",
                            path=f"$.class_derivations[{cd_name}].slot_derivations[{sd_name}]",
                            message=(
                                f"SlotDerivation '{sd_name}' sets both 'object_derivations' "
                                f"and 'class_derivations'. Remove 'object_derivations' and "
                                f"use 'class_derivations' only."
                            ),
                        )
                    )

    for ed in _iter_derivation_dicts(data.get("enum_derivations")):
        ed_name = ed.get("name", "<unnamed>")
        if ed.get("sources"):
            sources_counts["EnumDerivation"].append(ed_name)
        for pvd in _iter_derivation_dicts(ed.get("permissible_value_derivations")):
            pvd_name = pvd.get("name", "<unnamed>")
            if pvd.get("sources"):
                sources_counts["PermissibleValueDerivation"].append(pvd_name)
                if pvd.get("populated_from"):
                    messages.append(
                        ValidationMessage(
                            severity="error",
                            path=(f"$.enum_derivations[{ed_name}].permissible_value_derivations[{pvd_name}]"),
                            message=(
                                f"PermissibleValueDerivation '{pvd_name}' sets both "
                                f"'populated_from' and 'sources'. These are alternative "
                                f"spellings of the same field; set only 'populated_from' "
                                f"(which now accepts a list)."
                            ),
                        )
                    )

    for deriv_type, names in sources_counts.items():
        if names:
            preview = ", ".join(names[:5])
            suffix = f" (and {len(names) - 5} more)" if len(names) > 5 else ""
            messages.append(
                ValidationMessage(
                    severity="warning",
                    category="deprecated",
                    path=f"$.{deriv_type}",
                    message=(
                        f"{len(names)} {deriv_type}(s) use 'sources', which is deprecated: "
                        f"{preview}{suffix}. Use 'populated_from' instead. "
                        f"'sources' will be removed in a future version."
                    ),
                )
            )

    if object_derivation_names:
        preview = ", ".join(object_derivation_names[:5])
        suffix = f" (and {len(object_derivation_names) - 5} more)" if len(object_derivation_names) > 5 else ""
        messages.append(
            ValidationMessage(
                severity="warning",
                category="deprecated",
                path="$.SlotDerivation",
                message=(
                    f"{len(object_derivation_names)} SlotDerivation(s) use 'object_derivations', "
                    f"which is deprecated and flattened into 'class_derivations' at load time: "
                    f"{preview}{suffix}. Use list-based 'class_derivations' instead. "
                    f"'object_derivations' will be removed in a future version. "
                    f"See https://github.com/linkml/linkml-map/issues/112"
                ),
            )
        )

    if derived_from_names:
        preview = ", ".join(derived_from_names[:5])
        suffix = f" (and {len(derived_from_names) - 5} more)" if len(derived_from_names) > 5 else ""
        messages.append(
            ValidationMessage(
                severity="warning",
                category="deprecated",
                path="$.SlotDerivation",
                message=(
                    f"{len(derived_from_names)} SlotDerivation(s) use 'derived_from', "
                    f"which is deprecated and ignored by the runtime: "
                    f"{preview}{suffix}. This field can be removed — source slot "
                    f"dependencies are derivable from 'expr'. 'derived_from' will "
                    f"be removed in a future version."
                ),
            )
        )

    return messages


def validate_spec_semantics(
    data: dict[str, Any],
    *,
    source_schema: str | Path | None = None,
    target_schema: str | Path | None = None,
    source_schemaview: SchemaView | None = None,
    target_schemaview: SchemaView | None = None,
    strict: bool = False,
    spec_base_path: Path | None = None,
) -> list[ValidationMessage]:
    """Validate spec references against source and/or target schemas.

    Checks that class names, slot names, ``populated_from`` references, and
    expression slot references resolve against the provided schemas.

    Pre-loaded ``SchemaView`` instances take precedence over path-based
    arguments; pass them when the caller already has schemas in memory
    (e.g. CLI pre-flight after ``_load_specs``) to avoid re-fetching
    remote schemas or re-parsing large local ones.

    :param data: A **normalized** spec dict.
    :param source_schema: Path to the source LinkML schema (loaded only
        if ``source_schemaview`` is not provided).
    :param target_schema: Path to the target LinkML schema (loaded only
        if ``target_schemaview`` is not provided).
    :param source_schemaview: Pre-loaded source schema. Takes precedence
        over ``source_schema``.
    :param target_schemaview: Pre-loaded target schema. Takes precedence
        over ``target_schema``.
    :param strict: If ``True``, unresolved expression slot references are
        errors instead of warnings.
    :param spec_base_path: Directory for resolving relative schema paths
        found in the spec's ``source_schema``/``target_schema`` fields.
    :returns: A list of validation messages.
    """
    messages: list[ValidationMessage] = []

    source_sv: SchemaView | None = source_schemaview
    target_sv: SchemaView | None = target_schemaview

    if source_sv is None:
        source_path, source_explicit = _resolve_schema_path(data.get("source_schema"), source_schema, spec_base_path)
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

    if target_sv is None:
        target_path, target_explicit = _resolve_schema_path(data.get("target_schema"), target_schema, spec_base_path)
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

    # Join aliases — names like "demographics" in {demographics.age} that
    # reference a joined table, not a slot on the source class. Excluded
    # from expression-reference validation to avoid false-positive warnings.
    joins = cd.get("joins") or {}
    joined_aliases: set[str] = set(joins.keys()) if isinstance(joins, dict) else set()

    for sd in slot_derivation_dicts:
        _validate_slot_derivation(
            sd,
            cd_name,
            cd_path,
            source_class_slots,
            target_class_slots,
            joined_aliases,
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
    joined_aliases: set[str],
    strict: bool,
    messages: list[ValidationMessage],
) -> None:
    """Validate a single slot derivation against schemas.

    :param joined_aliases: Names declared in the parent class derivation's
        ``joins`` mapping. Expression references to these names (e.g.
        ``{demographics.age}``) are skipped — they refer to joined tables,
        not source-class slots.
    """
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

    # Expression slot references — skip join aliases, they reference joined
    # tables (validated against the joined class is a separate enhancement).
    expr = sd.get("expr")
    if expr is not None and source_class_slots is not None:
        refs = extract_expr_slot_references(expr) - joined_aliases
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
    normalized, scan_messages = _normalize_and_collect_messages(data)
    messages = _validate_structural(normalized, schema_path=schema_path)
    if not messages:
        messages.extend(scan_messages)
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
