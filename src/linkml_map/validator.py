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
from typing import Any, Literal, NamedTuple

import jsonschema
import yaml
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime import SchemaView

from linkml_map.datamodel import TR_SCHEMA
from linkml_map.transformer.transformer import Transformer
from linkml_map.utils.eval_utils import FUNCTIONS
from linkml_map.utils.join_utils import resolve_join

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


class _ExprScan(NamedTuple):
    """Structural facts collected from a single walk of an expression AST.

    :ivar slot_refs: Bare ``x`` / ``{x}`` / ``src.x`` slot references, with
        safe and locally bound names removed.
    :ivar attribute_refs: ``base.attr`` accesses (excluding ``src`` and safe
        bases), as a mapping of base name to the attribute names accessed.
    :ivar arithmetic_slots: Slot names used as a direct operand of a
        non-additive arithmetic operator, with safe and bound names removed.
    """

    slot_refs: set[str]
    attribute_refs: dict[str, set[str]]
    arithmetic_slots: set[str]


# Arithmetic operators whose string operands the evaluator silently coerces to
# numbers (see linkml/linkml-map#285). ``+`` is deliberately excluded: it is
# also string concatenation, so a string operand there is often intended (#289).
_ARITHMETIC_BINOPS = (ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)


def _operand_slot_name(node: ast.expr) -> str | None:
    """Return the slot name a BinOp operand references directly, else ``None``.

    Recognizes only the three direct-reference forms — bare ``x``, ``{x}``
    (parsed as an ``ast.Set`` of one ``ast.Name``), and ``src.x`` — so a slot
    buried in a call like ``str({x})`` is not treated as an arithmetic operand.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Set) and len(node.elts) == 1 and isinstance(node.elts[0], ast.Name):
        return node.elts[0].id
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "src":
        return node.attr
    return None


def _scan_expr(expr: str) -> _ExprScan:
    """Collect every expression fact the validator needs in one AST walk.

    The validator needs three different views of the same expression — slot
    references, attribute references, and arithmetic-operand slots. Collecting
    them in a single parse-and-walk (rather than one walk per view) keeps the
    hot path to a single traversal; the public ``extract_expr_*`` helpers are
    thin wrappers over this.

    :param expr: A LinkML expression string.
    :returns: An :class:`_ExprScan` of the collected structural facts.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        try:
            tree = ast.parse(expr, mode="exec")
        except SyntaxError:
            return _ExprScan(set(), {}, set())

    names: set[str] = set()
    bound: set[str] = set()
    attribute_refs: dict[str, set[str]] = {}
    arithmetic: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                bound.add(node.id)
            else:
                names.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base = node.value.id
            if base == "src":
                names.add(node.attr)
            elif base not in _EXPR_SAFE_NAMES:
                attribute_refs.setdefault(base, set()).add(node.attr)
        elif isinstance(node, ast.comprehension) and isinstance(node.target, ast.Name):
            bound.add(node.target.id)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, _ARITHMETIC_BINOPS):
            for operand in (node.left, node.right):
                slot = _operand_slot_name(operand)
                if slot is not None:
                    arithmetic.add(slot)

    safe_and_bound = _EXPR_SAFE_NAMES | bound
    return _ExprScan(
        slot_refs=names - safe_and_bound,
        attribute_refs=attribute_refs,
        arithmetic_slots=arithmetic - safe_and_bound,
    )


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
    return _scan_expr(expr).slot_refs


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
    return _scan_expr(expr).attribute_refs


def extract_expr_arithmetic_slots(expr: str) -> set[str]:
    """Extract slot names used as a direct operand of an arithmetic operator.

    Only the non-additive operators (``*``, ``-``, ``/``, ``//``, ``%``,
    ``**``) count, and only direct references (``x``, ``{x}``, ``src.x``) — a
    slot inside a call such as ``str({x})`` is not an operand. ``+`` is
    excluded because it doubles as string concatenation. Used to warn when a
    string-typed slot is silently coerced to a number in arithmetic (#289).

    :param expr: A LinkML expression string.
    :returns: A set of slot names used directly in non-additive arithmetic.

    Example::

        >>> sorted(extract_expr_arithmetic_slots("{col} * 365"))
        ['col']
        >>> sorted(extract_expr_arithmetic_slots("({days} * 365) + offset"))
        ['days']
        >>> extract_expr_arithmetic_slots("str({col}) + ' yrs'")
        set()
        >>> sorted(extract_expr_arithmetic_slots("{a} - {b}"))
        ['a', 'b']
    """
    return _scan_expr(expr).arithmetic_slots


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


def _resolve_schemaview(
    preloaded: SchemaView | None,
    spec_value: dict | None,
    explicit: str | Path | None,
    base_path: Path | None,
    label: str,
    messages: list[ValidationMessage],
) -> SchemaView | None:
    """Resolve a single (source or target) schema view, loading it if needed.

    Returns ``preloaded`` unchanged when a SchemaView was already supplied.
    Otherwise resolves a path via :func:`_resolve_schema_path` and loads it,
    appending a message to ``messages`` on failure (``error`` when the path
    was explicitly provided by the user, ``warning`` when auto-detected).

    :param preloaded: A pre-loaded SchemaView, or ``None`` to resolve a path.
    :param spec_value: The ``source_schema``/``target_schema`` spec field.
    :param explicit: An explicitly provided schema path (overrides the spec).
    :param base_path: Directory for resolving relative paths.
    :param label: ``"source_schema"`` or ``"target_schema"`` — used as the
        message path and in the failure text.
    :param messages: List to append a load-failure message to.
    :returns: The resolved SchemaView, or ``None`` if none was available.
    """
    if preloaded is not None:
        return preloaded
    path, explicit_provided = _resolve_schema_path(spec_value, explicit, base_path)
    if not path:
        return None
    try:
        return _load_schemaview_with_timeout(path)
    except Exception as exc:
        messages.append(
            ValidationMessage(
                severity="error" if explicit_provided else "warning",
                path=label,
                message=f"Could not load {label.replace('_', ' ')} '{path}': {exc}",
            )
        )
        return None


def _iter_derivation_dicts(raw: Any) -> list[dict[str, Any]]:
    """Normalize a derivations section (dict or list) to a list of dicts.

    Assumes the SHAPE phase of ``Transformer._normalize_spec_dict`` has
    already canonicalized compact-key list items, so callers only need to
    handle dict-keyed and explicit-name list forms here.
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

    Runs in the SCAN phase of ``Transformer._normalize_spec_dict`` — after
    SHAPE (which runs ``ReferenceValidator.normalize()`` and the local
    compact-key pre-expansion) and before MIGRATE (which flattens
    ``object_derivations``, inherits ``populated_from``, and rewrites PV
    ``sources``). So the dict the scan sees is structurally canonical
    (dict-keyed or explicit-name list, no compact-key items) but the
    deprecated field values are still as the user wrote them.

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
    * ``source_schema`` / ``target_schema`` set to a bare string — the
      original form, now superseded by the ``SchemaReference`` object
      form (``{name: ...}``). Coerced at load time. Severity: warning,
      category: deprecated.

    ``sources`` deprecation findings are collapsed to one message per
    (deprecation, derivation type) pair to keep output readable on
    large specs; per-entry messages are emitted for the other categories.

    :param data: A spec dict post-SHAPE, pre-MIGRATE. Derivation sections
        are dict-keyed or explicit-name list (no compact-key items).
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

    for schema_field in ("source_schema", "target_schema"):
        if isinstance(data.get(schema_field), str):
            messages.append(
                ValidationMessage(
                    severity="warning",
                    category="deprecated",
                    path=f"$.{schema_field}",
                    message=(
                        f"'{schema_field}' is set to a bare string, which is deprecated. "
                        f"Use the SchemaReference object form '{schema_field}: {{name: ...}}'. "
                        f"The string form will be removed in a future version."
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

    source_sv = _resolve_schemaview(
        source_schemaview, data.get("source_schema"), source_schema, spec_base_path, "source_schema", messages
    )
    target_sv = _resolve_schemaview(
        target_schemaview, data.get("target_schema"), target_schema, spec_base_path, "target_schema", messages
    )

    if source_sv is None and target_sv is None:
        return messages

    # Top-level class_derivation name pool — used to resolve is_a / mixins
    # references against spec-internal derivations (#219). Matches the
    # runtime's _find_class_derivation_by_name which only inspects the
    # top-level CD list.
    derivation_pool = _collect_class_derivation_pool(data)

    # Precompute once and thread through the recursion: every nested CD
    # would otherwise rebuild these in _build_joined_class_map,
    # _check_cross_table_join, and _check_class_inheritance_refs.
    source_all_classes = set(source_sv.all_classes()) if source_sv is not None else set()
    target_all_classes = set(target_sv.all_classes()) if target_sv is not None else set()

    # Validate class_derivations (recurses into nested CDs internally)
    for cd in _iter_derivation_dicts(data.get("class_derivations", [])):
        _validate_class_derivation(
            cd,
            source_sv,
            target_sv,
            strict,
            messages,
            derivation_pool=derivation_pool,
            source_all_classes=source_all_classes,
            target_all_classes=target_all_classes,
        )

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


def _slot_is_string_typed(sv: SchemaView, range_name: str | None) -> bool:
    """True if a range resolves to a string-based scalar type.

    These are the ranges the evaluator silently coerces when they meet a
    number in arithmetic (see linkml/linkml-map#285) — e.g. a column declared
    ``string`` that holds numeric-looking text. Classes, enums, numeric types,
    and unresolvable ranges all return ``False``: only string-based *types* are
    in scope, matching the runtime's ``isinstance(value, str)`` coercion path.
    Custom types resolve through their ancestors, so ``typeof: string`` counts.

    :param sv: The source schema view.
    :param range_name: The slot's declared range, or ``None``.
    :returns: ``True`` if the range is a string-based scalar type.
    """
    if range_name is None or range_name not in sv.all_types():
        return False
    for ancestor in sv.type_ancestors(range_name):
        ancestor_type = sv.get_type(ancestor)
        if ancestor_type is not None and ancestor_type.base == "str":
            return True
    return False


def _validate_class_derivation(
    cd: dict[str, Any],
    source_sv: SchemaView | None,
    target_sv: SchemaView | None,
    strict: bool,
    messages: list[ValidationMessage],
    parent_class_deriv: dict[str, Any] | None = None,
    parent_path: str = "",
    derivation_pool: set[str] | None = None,
    source_all_classes: set[str] | None = None,
    target_all_classes: set[str] | None = None,
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
    :param source_all_classes: Precomputed ``set(source_sv.all_classes())``,
        shared across recursion so each nested CD doesn't rebuild it.
        ``None`` triggers a local computation (callers outside the
        public entrypoint).
    :param target_all_classes: Precomputed ``set(target_sv.all_classes())``,
        same rationale as ``source_all_classes``.
    """
    if source_all_classes is None:
        source_all_classes = set(source_sv.all_classes()) if source_sv is not None else set()
    if target_all_classes is None:
        target_all_classes = set(target_sv.all_classes()) if target_sv is not None else set()
    cd_name = cd.get("name", "?")
    cd_path = f"{parent_path}.class_derivations[{cd_name}]" if parent_path else f"class_derivations[{cd_name}]"

    # Cross-table check for nested CDs (closes #211): does the nested CD's
    # populated_from differ from its parent's, and can the join be resolved?
    if parent_class_deriv is not None:
        _check_cross_table_join(cd, parent_class_deriv, source_sv, cd_path, messages, source_all_classes)

    # is_a / mixins resolution check (closes #219).
    if derivation_pool is not None:
        _check_class_inheritance_refs(cd, cd_path, derivation_pool, target_sv, messages, target_all_classes)

    # Target: class name should exist
    target_class_slots: set[str] | None = None
    if target_sv is not None:
        if cd_name not in target_all_classes:
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
    source_string_scalar_slots: set[str] | None = None
    resolved_source_class: str | None = None
    if source_sv is not None and source_class is not None:
        if source_class not in source_all_classes:
            messages.append(
                ValidationMessage(
                    severity="error",
                    path=cd_path,
                    message=f"Source class '{source_class}' (populated_from) not found in source schema",
                )
            )
        else:
            resolved_source_class = source_class

    # If source_sv provided but no populated_from, fall back to match the runtime:
    # - Nested CDs without populated_from inherit the parent's effective source
    #   (see ObjectTransformer._derive_nested_objects, which feeds the parent's
    #   row through when the nested CD has no populated_from).
    # - Top-level CDs fall back to the identity case (cd_name == source class).
    if source_sv is not None and source_class is None and resolved_source_class is None:
        if parent_class_deriv is not None:
            fallback_class = parent_class_deriv.get("populated_from") or parent_class_deriv.get("name")
        else:
            fallback_class = cd_name
        if fallback_class and fallback_class in source_all_classes:
            resolved_source_class = fallback_class

    if resolved_source_class is not None:
        induced_source_slots = source_sv.class_induced_slots(resolved_source_class)
        source_class_slots = {s.name for s in induced_source_slots}
        # Single-valued, string-typed slots are the ones the evaluator silently
        # coerces in arithmetic (#285); flag their arithmetic use below. Skip
        # multivalued slots, whose ``*`` is genuine list repetition.
        source_string_scalar_slots = {
            s.name for s in induced_source_slots if not s.multivalued and _slot_is_string_typed(source_sv, s.range)
        }

    # Validate slot_derivations (may be list or dict after normalization)
    slot_derivation_dicts = _iter_derivation_dicts(cd.get("slot_derivations", []))

    # Build alias -> slot-set map for cross-table expression reference checks.
    # Covers both explicit `joins:` aliases and the nested-CD populated_from
    # targets that #212's normalization will synthesize joins for.
    joined_class_slots = _build_joined_class_map(cd, source_sv, slot_derivation_dicts, source_all_classes)

    for sd in slot_derivation_dicts:
        sd_name = sd.get("name", "?")
        sd_path = f"{cd_path}.slot_derivations[{sd_name}]"
        _validate_slot_derivation(
            sd,
            cd_name,
            cd_path,
            source_class_slots,
            source_string_scalar_slots,
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
                source_all_classes=source_all_classes,
                target_all_classes=target_all_classes,
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
    source_all_classes: set[str],
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
    :param source_all_classes: Precomputed ``set(source_sv.all_classes())``
        threaded from the validation entrypoint.
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
            if source_sv is not None and joined_class in source_all_classes:
                slots = {s.name for s in source_sv.class_induced_slots(joined_class)}
                result[alias] = (joined_class, slots)
            else:
                result[alias] = (joined_class, None)

    # Identity case: when populated_from is omitted, the runtime treats the
    # CD's own name as the parent source. Match that behavior here so nested
    # CDs reachable from an identity-CD still get cross-table validation.
    parent_source = cd.get("populated_from") or cd.get("name")
    if source_sv is not None and parent_source:
        for sd in slot_derivation_dicts:
            for nested in _iter_derivation_dicts(sd.get("class_derivations", [])):
                nested_source = nested.get("populated_from")
                if nested_source and nested_source != parent_source and nested_source not in result:
                    if nested_source in source_all_classes:
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
    source_all_classes: set[str],
) -> None:
    """Diagnose nested CDs that reference a different source table than their parent.

    Closes #211 at validate-spec time. Mirrors the runtime synthesis logic
    in :class:`~linkml_map.transformer.transformer.Transformer`:

    - Explicit ``joins:`` covers the nested source → verify its keys.
    - No explicit join, :func:`~linkml_map.utils.join_utils.resolve_join`
      returns a key → ``info`` (will auto-synthesize at runtime).
    - No explicit join, :func:`~linkml_map.utils.join_utils.resolve_join`
      returns a reason → ``warning`` with the same diagnostic the runtime
      would raise.

    When run against the *derived* spec (post-synthesis), synthesized joins are
    already explicit, so the first branch handles them and no prediction occurs.
    """
    nested_source = nested_cd.get("populated_from")
    # Identity case for the parent: fall back to its name when populated_from
    # is omitted (matches _derive_nested_objects in the runtime).
    parent_source = parent_cd.get("populated_from") or parent_cd.get("name")
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
        elif source_sv is not None and parent_source in source_all_classes and nested_source in source_all_classes:
            # Keys are declared — verify they exist on the respective source
            # classes. A typo'd key passes the structural check but produces
            # silent nulls at runtime: ``source_obj.get(missing_key)`` returns
            # None, the join match fails, cross-table values resolve to null.
            parent_slots = {s.name for s in source_sv.class_induced_slots(parent_source)}
            nested_slots = {s.name for s in source_sv.class_induced_slots(nested_source)}
            if join_on:
                key_checks = [(join_on, parent_slots, parent_source), (join_on, nested_slots, nested_source)]
                key_label = "join_on"
            else:
                key_checks = [(source_key, parent_slots, parent_source), (lookup_key, nested_slots, nested_source)]
            for i, (key_value, slot_set, class_name) in enumerate(key_checks):
                if key_value in slot_set:
                    continue
                if not join_on:
                    key_label = "source_key" if i == 0 else "lookup_key"
                messages.append(
                    ValidationMessage(
                        severity="warning",
                        path=nested_path,
                        message=(
                            f"Join spec for '{nested_source}': "
                            f"'{key_label}={key_value}' is not a slot on source class "
                            f"'{class_name}'. Runtime will silently resolve cross-table "
                            f"values to null."
                        ),
                    )
                )
        return

    if source_sv is None:
        return

    if parent_source not in source_all_classes or nested_source not in source_all_classes:
        # Missing-class errors are emitted elsewhere; can't predict joinability.
        return

    resolution = resolve_join(source_sv, parent_source, nested_source)
    if resolution.key is not None:
        messages.append(
            ValidationMessage(
                severity="info",
                path=nested_path,
                message=(
                    f"Nested 'populated_from={nested_source}' differs from parent "
                    f"'populated_from={parent_source}'. No explicit join entry for "
                    f"'{nested_source}'; implicit join will be synthesized on column "
                    f"'{resolution.key}'. Consider declaring the join explicitly."
                ),
            )
        )
        return

    reason = resolution.reason
    messages.append(
        ValidationMessage(
            severity="warning",
            path=nested_path,
            message=(
                f"Nested 'populated_from={nested_source}' differs from parent "
                f"'populated_from={parent_source}', but no implicit join can be "
                f"synthesized: {reason}. Add an explicit join entry for "
                f"'{nested_source}' — cross-table values will otherwise resolve to null."
            ),
        )
    )


def _check_class_inheritance_refs(
    cd: dict[str, Any],
    cd_path: str,
    derivation_pool: set[str],
    target_sv: SchemaView | None,
    messages: list[ValidationMessage],
    target_all_classes: set[str],
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

    for field_label, parent_name in parents:
        if parent_name in derivation_pool:
            continue
        if parent_name in target_all_classes:
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
    source_string_scalar_slots: set[str] | None,
    target_class_slots: set[str] | None,
    joined_class_slots: dict[str, tuple[str, set[str] | None]],
    strict: bool,
    messages: list[ValidationMessage],
) -> None:
    """Validate a single slot derivation against schemas.

    :param source_string_scalar_slots: Names of single-valued, string-typed
        slots on the source class. Arithmetic use of these is silently
        coerced to a number at runtime (#285), so it is surfaced as a
        warning. ``None`` when no source schema is available, in which case
        the check is skipped entirely.
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

    # One AST walk feeds all three expression checks below (slot refs,
    # arithmetic operands, and attribute refs).
    scan = _scan_expr(expr)

    # Bare-name expression refs — exclude join aliases (they're a "base", not
    # a slot on the source class).
    refs = scan.slot_refs - joined_aliases
    for ref in sorted(refs):
        if ref not in source_class_slots:
            messages.append(
                ValidationMessage(
                    severity="error" if strict else "warning",
                    path=sd_path,
                    message=f"Expression references '{ref}' which is not a slot on the source class",
                )
            )

    # String-typed source slots used directly in arithmetic are silently
    # coerced to numbers at runtime (#285); surface it so a curator can
    # re-type the slot. Coercion is always the correct runtime outcome, so
    # this is a warning unless the caller opted into strict.
    if source_string_scalar_slots:
        for slot in sorted(scan.arithmetic_slots & source_string_scalar_slots):
            messages.append(
                ValidationMessage(
                    severity="error" if strict else "warning",
                    path=sd_path,
                    message=(
                        f"Expression uses '{slot}' in arithmetic, but it is declared with a "
                        f"non-numeric range on the source class; its value is coerced to a number "
                        f"at runtime. Declare a numeric range to make the intent explicit."
                    ),
                    category="type-coercion",
                )
            )

    # Cross-table attribute refs — partial #213 coverage: {alias.field}
    # validated against the joined class's slots when known.
    attr_refs = scan.attribute_refs
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
