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

    severity: Literal["error", "warning", "info"]
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


def extract_expr_attribute_references(expr: str) -> dict[str, set[str]]:
    """Extract ``base.attr`` accesses from a LinkML expression.

    Used to validate cross-table references like ``{joined_table.field}``
    against the joined class's slot list. The ``src.attr`` form is excluded
    because :func:`extract_expr_slot_references` already treats it as a bare
    slot reference on the source class.

    :param expr: A LinkML expression string.
    :returns: Mapping of base name to the set of attributes accessed on it.

    Example::

        >>> result = extract_expr_attribute_references("{demographics.age}")
        >>> sorted(result["demographics"])
        ['age']
        >>> extract_expr_attribute_references("plain_var")
        {}
        >>> extract_expr_attribute_references("src.foo")
        {}
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        try:
            tree = ast.parse(expr, mode="exec")
        except SyntaxError:
            return {}

    result: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base = node.value.id
            if base == "src" or base in _EXPR_SAFE_NAMES:
                continue
            result.setdefault(base, set()).add(node.attr)
    return result


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

    Auto-detection from a spec value supports **local file paths** (relative
    to the spec file or absolute) and **URLs** (any value containing
    ``://``). Identifier-style values (e.g. ``source_schema: biolink``) are
    *not* auto-resolved — pass ``--source-schema`` / ``--target-schema``
    explicitly to point at a real file or URL for those cases. Skipping
    silently here prevents typos from triggering surprise network requests
    during validation.

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
    # Identifier-style values (no path, no URL): skip auto-detection.
    logger.debug(
        "Schema value %r is neither a resolvable path nor a URL; skipping auto-detection. "
        "Pass --source-schema / --target-schema to validate against this schema.",
        spec_value,
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
    """Check a normalized spec dict for use of deprecated fields.

    Currently flags two deprecations:

    * ``sources`` on ``ClassDerivation`` / ``SlotDerivation`` /
      ``EnumDerivation`` / ``PermissibleValueDerivation`` — replaced by
      ``populated_from``.
    * ``derived_from`` on ``SlotDerivation`` — ignored by the runtime
      and removable.

    Findings are collapsed to one message per (deprecation, derivation
    type) pair to keep output readable on large specs.

    Other deprecations (``object_derivations`` flattening) are surfaced
    during normalization in ``Transformer._normalize_slot_class_derivations``
    and do not need to be re-emitted here.

    :param data: A **normalized** spec dict (post ``normalize_spec_dict``).
    :returns: A list of warning messages with ``category="deprecated"``.
    """
    messages: list[ValidationMessage] = []
    sources_counts: dict[str, list[str]] = {
        "ClassDerivation": [],
        "SlotDerivation": [],
        "EnumDerivation": [],
        "PermissibleValueDerivation": [],
    }
    derived_from_names: list[str] = []

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

    for ed in _iter_derivation_dicts(data.get("enum_derivations")):
        ed_name = ed.get("name", "<unnamed>")
        if ed.get("sources"):
            sources_counts["EnumDerivation"].append(ed_name)
        for pvd in _iter_derivation_dicts(ed.get("permissible_value_derivations")):
            pvd_name = pvd.get("name", "<unnamed>")
            if pvd.get("sources"):
                sources_counts["PermissibleValueDerivation"].append(pvd_name)

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

    # Top-level class_derivation name pool — used to resolve is_a / mixins
    # references against spec-internal derivations (#219). Matches the
    # runtime's _find_class_derivation_by_name which only inspects the
    # top-level CD list.
    derivation_pool = _collect_class_derivation_pool(data)

    # Validate class_derivations (recurses into nested CDs internally)
    for cd in _iter_derivation_dicts(data.get("class_derivations", [])):
        _validate_class_derivation(cd, source_sv, target_sv, strict, messages, derivation_pool=derivation_pool)

    # Validate enum_derivations
    for ed in _iter_derivation_dicts(data.get("enum_derivations", [])):
        _validate_enum_derivation(ed, source_sv, target_sv, messages)

    return messages


def _collect_class_derivation_pool(data: dict[str, Any]) -> set[str]:
    """Names of all top-level class_derivations in the spec.

    This is the pool used to resolve ``is_a`` and ``mixins`` references
    against spec-internal derivations (#219). Only top-level CDs are
    included, matching the runtime's
    :meth:`~linkml_map.transformer.transformer.Transformer._find_class_derivation_by_name`
    which raises ``KeyError`` for anything not at the top level.
    """
    return {cd.get("name") for cd in _iter_derivation_dicts(data.get("class_derivations", [])) if cd.get("name")}


def _validate_class_derivation(
    cd: dict[str, Any],
    source_sv: SchemaView | None,
    target_sv: SchemaView | None,
    strict: bool,
    messages: list[ValidationMessage],
    parent_class_deriv: dict[str, Any] | None = None,
    parent_path: str = "",
    derivation_pool: set[str] | None = None,
) -> None:
    """Validate a single class derivation against schemas.

    Recurses into nested ``class_derivations`` declared under any slot
    derivation, threading the parent CD through so cross-table references
    (#211) can be diagnosed.

    :param parent_class_deriv: For nested CDs, the enclosing class
        derivation's dict. ``None`` for top-level CDs.
    :param parent_path: Path prefix for nested validation messages
        (e.g. ``class_derivations[Outer].slot_derivations[inner]``).
        Empty string for top-level CDs.
    :param derivation_pool: Names of all top-level class_derivations in
        the spec. Used to resolve ``is_a``/``mixins`` (#219). ``None``
        skips the check.
    """
    cd_name = cd.get("name", "?")
    cd_path = f"{parent_path}.class_derivations[{cd_name}]" if parent_path else f"class_derivations[{cd_name}]"

    # Cross-table check for nested CDs (closes #211): does the nested CD's
    # populated_from differ from its parent's, and can the join be resolved?
    if parent_class_deriv is not None:
        _check_cross_table_join(cd, parent_class_deriv, source_sv, cd_path, messages)

    # is_a / mixins resolution check (closes #219).
    if derivation_pool is not None:
        _check_class_inheritance_refs(cd, cd_path, derivation_pool, target_sv, messages)

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

    # Build alias -> slot-set map for cross-table expression reference checks.
    # Covers both explicit `joins:` aliases and the nested-CD populated_from
    # targets that #212's normalization will synthesize joins for.
    joined_class_slots = _build_joined_class_map(cd, source_sv, slot_derivation_dicts)

    for sd in slot_derivation_dicts:
        sd_name = sd.get("name", "?")
        sd_path = f"{cd_path}.slot_derivations[{sd_name}]"
        _validate_slot_derivation(
            sd,
            cd_name,
            cd_path,
            source_class_slots,
            target_class_slots,
            joined_class_slots,
            strict,
            messages,
        )

        # Recurse into nested class_derivations declared on this slot.
        for nested_cd in _iter_derivation_dicts(sd.get("class_derivations", [])):
            _validate_class_derivation(
                nested_cd,
                source_sv,
                target_sv,
                strict,
                messages,
                parent_class_deriv=cd,
                parent_path=sd_path,
                derivation_pool=derivation_pool,
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


def _build_joined_class_map(
    cd: dict[str, Any],
    source_sv: SchemaView | None,
    slot_derivation_dicts: list[dict[str, Any]],
) -> dict[str, tuple[str, set[str] | None]]:
    """Map alias names to the resolved joined-class name and its slot set.

    Combines two sources of "joined tables" visible from this CD's
    expressions:

    1. Explicit ``joins:`` aliases on this CD. The joined class is
       ``joins[alias].class_named`` if set, otherwise the alias name.
    2. Implicit join targets — nested ``class_derivations`` whose
       ``populated_from`` differs from this CD's, which the engine's
       normalization pass (#212) will auto-resolve.

    :param cd: This class derivation dict.
    :param source_sv: Source schema view, or ``None``.
    :param slot_derivation_dicts: Pre-iterated slot derivations (avoids
        re-walking).
    :returns: Mapping of alias name to a ``(joined_class_name, slot_set)``
        tuple. ``slot_set`` is ``None`` when the joined class can't be
        resolved in the source schema (or when no source schema is
        available). The class name is tracked separately so error
        messages can distinguish alias from class for explicit
        ``class_named`` joins.
    """
    result: dict[str, tuple[str, set[str] | None]] = {}

    joins = cd.get("joins") or {}
    if isinstance(joins, dict):
        for alias, spec in joins.items():
            joined_class: str
            if isinstance(spec, dict):
                joined_class = spec.get("class_named") or alias
            else:
                joined_class = alias
            if source_sv is not None and joined_class in set(source_sv.all_classes()):
                slots = {s.name for s in source_sv.class_induced_slots(joined_class)}
                result[alias] = (joined_class, slots)
            else:
                result[alias] = (joined_class, None)

    parent_source = cd.get("populated_from")
    if source_sv is not None and parent_source:
        all_classes = set(source_sv.all_classes())
        for sd in slot_derivation_dicts:
            for nested in _iter_derivation_dicts(sd.get("class_derivations", [])):
                nested_source = nested.get("populated_from")
                if nested_source and nested_source != parent_source and nested_source not in result:
                    if nested_source in all_classes:
                        slots = {s.name for s in source_sv.class_induced_slots(nested_source)}
                        result[nested_source] = (nested_source, slots)
                    else:
                        result[nested_source] = (nested_source, None)

    return result


def _check_cross_table_join(
    nested_cd: dict[str, Any],
    parent_cd: dict[str, Any],
    source_sv: SchemaView | None,
    nested_path: str,
    messages: list[ValidationMessage],
) -> None:
    """Diagnose nested CDs that reference a different source table than their parent.

    Closes #211 at validate-spec time. Mirrors the runtime synthesis logic
    in :class:`~linkml_map.transformer.transformer.Transformer`:

    - Explicit ``joins:`` covers the nested source → no message.
    - No explicit join, :func:`~linkml_map.utils.join_utils.pick_join_key`
      returns a column → ``info`` (#212 will auto-synthesize at runtime).
    - No explicit join, no implicit join can be synthesized → ``warning``
      with the same diagnostic the runtime would raise.
    """
    nested_source = nested_cd.get("populated_from")
    parent_source = parent_cd.get("populated_from")
    if not nested_source or not parent_source or nested_source == parent_source:
        return

    parent_joins = parent_cd.get("joins") or {}
    if isinstance(parent_joins, dict) and nested_source in parent_joins:
        # Explicit join is present — verify the spec carries enough keys to
        # actually resolve a row, mirroring the runtime check in
        # ``_resolve_joined_row``. A structurally-valid-but-empty entry like
        # ``joins: {Reading: {}}`` would otherwise pass validation but blow
        # up at transform time with ``ValueError: Join spec ... must
        # specify 'join_on' or both 'source_key' and 'lookup_key'``.
        spec = parent_joins[nested_source]
        spec_dict = spec if isinstance(spec, dict) else {}
        join_on = spec_dict.get("join_on")
        source_key = spec_dict.get("source_key")
        lookup_key = spec_dict.get("lookup_key")
        if not join_on and not (source_key and lookup_key):
            messages.append(
                ValidationMessage(
                    severity="warning",
                    path=nested_path,
                    message=(
                        f"Join spec for '{nested_source}' is missing keys: "
                        f"must specify 'join_on' or both 'source_key' and "
                        f"'lookup_key'. Runtime will raise ValueError."
                    ),
                )
            )
        return

    if source_sv is None:
        return

    from linkml_map.utils.join_utils import find_common_columns, pick_join_key

    all_classes = set(source_sv.all_classes())
    if parent_source not in all_classes or nested_source not in all_classes:
        # Missing-class errors are emitted elsewhere; can't predict joinability.
        return

    key = pick_join_key(source_sv, parent_source, nested_source)
    if key is not None:
        messages.append(
            ValidationMessage(
                severity="info",
                path=nested_path,
                message=(
                    f"Nested 'populated_from={nested_source}' differs from parent "
                    f"'populated_from={parent_source}'. No explicit joins: block; "
                    f"implicit join will be synthesized on column '{key}'. "
                    f"Consider declaring the join explicitly."
                ),
            )
        )
        # Surface the column-overlap hazard for #217 Bug 2 (data-dependent
        # ambiguity). When parent and child share non-join columns, runtime
        # behavior depends on whether the join lookup hits: a match merges
        # rows and marks shared columns _AMBIGUOUS (unqualified access
        # errors), but a miss leaves the bare parent row in place and
        # silently returns the parent's value for that column. Flag it
        # statically so users disambiguate before sparse data exposes it.
        parent_slots = {s.name for s in source_sv.class_induced_slots(parent_source)}
        nested_slots = {s.name for s in source_sv.class_induced_slots(nested_source)}
        overlap = (parent_slots & nested_slots) - {key}
        if overlap:
            shared = ", ".join(f"'{c}'" for c in sorted(overlap))
            messages.append(
                ValidationMessage(
                    severity="warning",
                    path=nested_path,
                    message=(
                        f"Implicit join between '{parent_source}' and '{nested_source}' "
                        f"on '{key}' — overlapping non-join columns {{{shared}}} will "
                        f"resolve ambiguously: error on rows with a join match "
                        f"(_AMBIGUOUS sentinel), silent parent value on rows without "
                        f"(#217). Disambiguate with an explicit joins: alias or "
                        f"dotted-reference form."
                    ),
                )
            )
        return

    common = find_common_columns(source_sv, parent_source, nested_source)
    if not common:
        reason = f"no columns are shared between '{parent_source}' and '{nested_source}'"
    else:
        candidates = ", ".join(f"'{c}'" for c in sorted(common))
        reason = (
            f"multiple candidate join columns are shared between '{parent_source}' "
            f"and '{nested_source}' ({candidates}); cannot pick automatically"
        )
    messages.append(
        ValidationMessage(
            severity="warning",
            path=nested_path,
            message=(
                f"Nested 'populated_from={nested_source}' differs from parent "
                f"'populated_from={parent_source}', but no implicit join can be "
                f"synthesized: {reason}. Add an explicit joins: block — cross-table "
                f"values will otherwise resolve to null."
            ),
        )
    )


def _check_class_inheritance_refs(
    cd: dict[str, Any],
    cd_path: str,
    derivation_pool: set[str],
    target_sv: SchemaView | None,
    messages: list[ValidationMessage],
) -> None:
    """Resolve ``is_a`` and ``mixins`` string references (closes #219).

    Each reference must resolve to either:

    1. A top-level ``class_derivation`` in this spec (matches the runtime's
       ``_find_class_derivation_by_name`` behavior), or
    2. A class in the target schema (matches LinkML's ``is_a`` convention
       on plain schemas).

    A reference that resolves to neither emits an ``error`` — but only when
    ``target_sv`` is available. Without the target schema, half the pool is
    unknown, so a miss against the spec pool alone is ambiguous (it could
    still be a valid target schema reference) and is left unchecked rather
    than risk a false positive.
    """
    parents: list[tuple[str, str]] = []
    is_a = cd.get("is_a")
    if isinstance(is_a, str):
        parents.append(("is_a", is_a))
    mixins = cd.get("mixins")
    if isinstance(mixins, list):
        parents.extend(("mixins", m) for m in mixins if isinstance(m, str))

    if not parents or target_sv is None:
        return

    target_classes = set(target_sv.all_classes())

    for field_label, parent_name in parents:
        if parent_name in derivation_pool:
            continue
        if parent_name in target_classes:
            continue
        messages.append(
            ValidationMessage(
                severity="error",
                path=cd_path,
                message=(
                    f"'{field_label}: {parent_name}' does not resolve to a "
                    f"class_derivation in this spec or a class in the target schema"
                ),
            )
        )


def _validate_slot_derivation(
    sd: dict[str, Any],
    parent_class_name: str,
    parent_path: str,
    source_class_slots: set[str] | None,
    target_class_slots: set[str] | None,
    joined_class_slots: dict[str, tuple[str, set[str] | None]],
    strict: bool,
    messages: list[ValidationMessage],
) -> None:
    """Validate a single slot derivation against schemas.

    :param joined_class_slots: Mapping of alias name (from explicit
        ``joins:`` or an implicit-join target) to a tuple of
        ``(joined_class_name, slot_set)``. Expression bare-name
        references to these aliases are excluded from source-class
        checks, and attribute references like ``{alias.field}`` are
        validated against the joined class's slot set. A ``slot_set``
        of ``None`` means the joined class couldn't be resolved — the
        bare alias is still tolerated, but attribute access is skipped.
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

    expr = sd.get("expr")
    if expr is None or source_class_slots is None:
        return

    joined_aliases = set(joined_class_slots.keys())

    # Bare-name expression refs — exclude join aliases (they're a "base", not
    # a slot on the source class).
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

    # Cross-table attribute refs — partial #213 coverage: {alias.field}
    # validated against the joined class's slots when known.
    attr_refs = extract_expr_attribute_references(expr)
    for base, attrs in attr_refs.items():
        if base not in joined_class_slots:
            continue
        joined_class, joined_slots = joined_class_slots[base]
        if joined_slots is None:
            continue
        # When the alias differs from the resolved class name (explicit
        # ``class_named``), surface both so the user knows which schema
        # class was actually checked.
        if joined_class == base:
            class_descriptor = f"joined class '{joined_class}'"
        else:
            class_descriptor = f"joined class '{joined_class}' (alias '{base}')"
        for attr in sorted(attrs):
            if attr not in joined_slots:
                messages.append(
                    ValidationMessage(
                        severity="error" if strict else "warning",
                        path=sd_path,
                        message=(
                            f"Expression references '{base}.{attr}' but '{attr}' is not a slot on {class_descriptor}"
                        ),
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
        messages.extend(check_deprecated_fields(normalized))
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
