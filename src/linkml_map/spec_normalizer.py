"""Load-time normalization of a raw transformation-specification dict.

Structural fixes applied to a raw dict before Pydantic instantiation — YAML
quirk handling, compact-key expansion, dict-to-list conversion, deprecated-field
migration. Requires no source schema; the schema-dependent half of
normalization (``populated_from``, ``range``, foreign-key induction) lives in
:meth:`~linkml_map.transformer.transformer.Transformer.derived_specification`.

Every entry point that turns YAML into a ``TransformationSpecification`` —
the transformer's load methods, :class:`~linkml_map.session.Session`,
:mod:`linkml_map.utils.loaders`, the CLI, and the validator — goes through
:func:`normalize_spec`.
"""

import warnings
from collections.abc import Iterator
from typing import Any

from linkml_runtime.processing.referencevalidator import ReferenceValidator
from linkml_runtime.utils.introspection import package_schemaview

from linkml_map.spec_scan import ValidationMessage, check_deprecated_fields
from linkml_map.transformer.errors import SpecificationError


def _iter_values_or_list(container: Any) -> Iterator[dict[str, Any]]:
    """Yield each dict in a derivations section (dict-keyed or list form).

    Doesn't expand compact-key list items — used both pre-SHAPE (where
    compact-key items are still present and the caller is responsible for
    expanding them via ``_expand_compact_keys`` if it needs to descend
    into them) and post-SHAPE (where everything is already canonical).
    """
    if isinstance(container, dict):
        for v in container.values():
            if isinstance(v, dict):
                yield v
    elif isinstance(container, list):
        for item in container:
            if isinstance(item, dict):
                yield item


def normalize_spec(obj: dict[str, Any], *, silent: bool = False) -> list[ValidationMessage]:
    """Normalize a raw specification dict in place. Return scan messages.

    Three clean phases, ordered so the SCAN sees a canonical shape with
    the user's original field values:

    1. **SHAPE** — pure structural canonicalization, no field semantics.
       Expands compact-key list forms everywhere they can appear
       (top-level class/enum derivations, nested class_derivations in
       slots, OD-inner class_derivations, PV-level lists), then runs
       ``ReferenceValidator`` for dict↔list canonicalization and name
       injection.
    2. **SCAN** — :func:`linkml_map.spec_scan.check_deprecated_fields`
       walks the canonical shape, returning ``ValidationMessage``
       records for deprecated-field usage and ambiguous combinations.
       Unless ``silent``, deprecation warnings fire as Python
       ``DeprecationWarning`` and conflict errors raise
       :class:`~linkml_map.transformer.errors.SpecificationError`.
    3. **MIGRATE** — all field semantics in one pass:
       ``object_derivations`` flatten, ``populated_from`` inheritance
       from parent class, PV scalar → list, PV explicit-``None`` strip,
       PV ``sources`` → ``populated_from`` (clearing ``sources``).

    After this function, ``sources`` no longer appears on any
    ``PermissibleValueDerivation`` — the runtime can rely on
    ``populated_from`` as the single source of truth.

    :param obj: Raw specification dict (e.g. from YAML or user code).
    :param silent: When ``True``, neither emit warnings nor raise on
        errors — return them in the message list instead. Used by the
        validator path so it can surface findings as
        ``ValidationMessage`` records.
    :returns: A list of :class:`ValidationMessage` records from the scan.
    """
    # SHAPE
    _shape_normalize(obj)

    # SCAN
    messages = check_deprecated_fields(obj)

    if not silent:
        errors = [m for m in messages if m.severity == "error"]
        if errors:
            raise SpecificationError("; ".join(m.message for m in errors))
        for m in messages:
            if m.category == "deprecated":
                warnings.warn(m.message, DeprecationWarning, stacklevel=3)

    # MIGRATE
    _flatten_object_derivations(obj)
    _inherit_populated_from(obj)
    _coerce_pv_populated_from_to_list(obj)
    _migrate_pv_sources_to_populated_from(obj)
    _coerce_schema_refs(obj)

    return messages


def _shape_normalize(obj: dict[str, Any]) -> None:
    """Canonicalize the structural shape of every derivation section.

    Expands compact-key list forms in every derivation-section location
    (including OD-inner class_derivations and PV-level lists, which
    ``ReferenceValidator`` doesn't canonicalize correctly), then runs
    ``ReferenceValidator`` for dict↔list canonicalization and name
    injection. No field semantics are mutated.
    """
    _pre_shape_expand_compact_keys(obj)
    normalizer = ReferenceValidator(package_schemaview("linkml_map.datamodel.transformer_model"))
    normalizer.expand_all = True
    normalized = normalize_transform_spec(obj, normalizer)
    obj.clear()
    obj.update(normalized)


def normalize_transform_spec(obj: dict[str, Any], normalizer: ReferenceValidator) -> dict:
    """Shape-canonicalize class_derivations recursively.

    Pure shape work — no field migrations. ``object_derivations``
    flattening and ``populated_from`` inheritance happen in the MIGRATE
    phase of :func:`normalize_spec` so the SCAN phase between them sees
    the user's original field values.
    """
    obj = normalizer.normalize(obj)

    class_derivations = obj.get("class_derivations", [])
    if isinstance(class_derivations, dict):
        cd_iter = class_derivations.values()
    else:
        cd_iter = class_derivations
    for class_spec in cd_iter:
        if not isinstance(class_spec, dict):
            continue
        slot_derivations = class_spec.get("slot_derivations", {})
        for slot_name, slot_spec in slot_derivations.items():
            if slot_spec.get("value") is not None and slot_spec.get("range") is None:
                slot_spec["range"] = "string"
            _normalize_slot_class_derivations(slot_name, slot_spec, normalizer)
    return obj


def _normalize_slot_class_derivations(
    slot_name: str,
    slot_spec: dict[str, Any],
    normalizer: ReferenceValidator,
) -> None:
    """Shape-canonicalize the ``class_derivations`` on a slot, recursively.

    Two steps, applied recursively to nested slots:

    1. Expand compact-key entries (``- Condition: {...}`` →
       ``{name: Condition, ...}``).
    2. Run the normalizer on each class derivation entry so dict-keyed
       ``slot_derivations`` get ``name`` injected and other shape
       canonicalization happens.

    Pure shape — no field semantics. ``object_derivations`` flattening
    and ``populated_from`` inheritance live in the MIGRATE phase of
    :func:`normalize_spec`, not here, so the SCAN phase sees the user's
    original field values.
    """
    slot_cd = slot_spec.get("class_derivations")
    if not isinstance(slot_cd, list):
        return

    _expand_compact_keys(slot_cd)

    for cd_entry in slot_cd:
        if not isinstance(cd_entry, dict):
            continue
        normalized = normalizer.normalize(cd_entry)
        cd_entry.clear()
        cd_entry.update(normalized)
        for nested_name, nested_sd in cd_entry.get("slot_derivations", {}).items():
            if isinstance(nested_sd, dict):
                _normalize_slot_class_derivations(nested_name, nested_sd, normalizer)


def _pre_shape_expand_compact_keys(obj: dict[str, Any]) -> None:
    """Recursively expand compact-key list forms before ReferenceValidator.

    Compact-key list form (``[{Name: {body}}]``) is a linkml-map convention,
    not a documented LinkML collection form. ``ReferenceValidator``
    therefore doesn't canonicalize it consistently — list-typed fields
    (top-level class_derivations) are left as-is, and dict-typed fields
    (permissible_value_derivations) get mangled to ``{None: ...}``. This
    pre-pass converts compact-key items to explicit-name form everywhere
    the linkml-map schema accepts a derivation section, so RV sees only
    LinkML-canonical input.

    See https://github.com/linkml/linkml/issues/3529 for the upstream
    behavior. The local pre-expansion makes us independent of how (or
    whether) that gets resolved.
    """
    _preprocess_class_derivations(obj)
    _preprocess_enum_derivations(obj)
    for cd in _iter_values_or_list(obj.get("class_derivations")):
        _expand_compact_keys_in_class_deriv(cd)


def _expand_compact_keys_in_class_deriv(cd: dict[str, Any]) -> None:
    """Expand compact-key list forms in a class derivation, recursively."""
    for sd in _iter_values_or_list(cd.get("slot_derivations")):
        # Slot's own nested class_derivations (list-with-compact-keys form)
        nested_cds = sd.get("class_derivations")
        if isinstance(nested_cds, list):
            _expand_compact_keys(nested_cds)
        for ncd in _iter_values_or_list(nested_cds):
            _expand_compact_keys_in_class_deriv(ncd)
        # OD-inner class_derivations (deprecated form; flattened in MIGRATE)
        ods = sd.get("object_derivations")
        if isinstance(ods, list):
            for od in ods:
                if not isinstance(od, dict):
                    continue
                od_cds = od.get("class_derivations")
                if isinstance(od_cds, list):
                    _expand_compact_keys(od_cds)
                for ncd in _iter_values_or_list(od_cds):
                    _expand_compact_keys_in_class_deriv(ncd)


def _preprocess_enum_derivations(obj: dict[str, Any]) -> None:
    """Pre-process top-level enum_derivations and their PV sections.

    Handles two compact-key cases ReferenceValidator doesn't:
    list-form enum_derivations with ``{Name: {...}}`` items, and
    list-form permissible_value_derivations with the same shape (which
    RV otherwise mangles into ``{None: ...}``).
    """
    eds = obj.get("enum_derivations")
    if isinstance(eds, dict):
        for k, v in eds.items():
            if v is None:
                eds[k] = {}
    elif isinstance(eds, list):
        _expand_compact_keys(eds)
    for ed in _iter_values_or_list(obj.get("enum_derivations")):
        pvs = ed.get("permissible_value_derivations")
        if isinstance(pvs, list):
            _expand_compact_keys(pvs)


def _preprocess_class_derivations(obj: dict[str, Any]) -> None:
    """Pre-process top-level class_derivations before ReferenceValidator normalization.

    Handles two cases:
    1. Dict format with None values (e.g. ``Entity:`` with no body) — replace
       with empty dicts so ReferenceValidator.ensure_list doesn't choke.
    2. List format with compact keys — delegate to ``_expand_compact_keys``.
    """
    cd = obj.get("class_derivations")
    if isinstance(cd, dict):
        for k, v in cd.items():
            if v is None:
                cd[k] = {}
    elif isinstance(cd, list):
        _expand_compact_keys(cd)


def _expand_compact_keys(items: list[dict[str, Any]]) -> None:
    """Expand YAML compact-key dicts in a list in place.

    Converts ``{"Condition": {"populated_from": "x"}}`` →
    ``{"name": "Condition", "populated_from": "x"}``.
    Skips items whose sole key is ``"name"`` (already expanded).
    """
    for i, item in enumerate(items):
        if isinstance(item, dict) and len(item) == 1:
            key, val = next(iter(item.items()))
            if key != "name" and isinstance(val, dict | type(None)):
                expanded = val if val is not None else {}
                expanded.setdefault("name", key)
                items[i] = expanded


def _flatten_object_derivations(obj: dict[str, Any]) -> None:
    """Flatten ``object_derivations`` into ``class_derivations`` on every slot.

    Conflicting specs (both ``object_derivations`` and ``class_derivations``
    set) are caught upstream by the SCAN phase as ``severity="error"``,
    so this function assumes a non-conflicting input.
    """
    for cd in _iter_values_or_list(obj.get("class_derivations")):
        _flatten_ods_in_class_deriv(cd)


def _flatten_ods_in_class_deriv(cd: dict[str, Any]) -> None:
    """Recursively walk a class derivation, flattening OD on each slot."""
    for sd in _iter_values_or_list(cd.get("slot_derivations")):
        ods = sd.get("object_derivations")
        if ods:
            flattened: list[dict[str, Any]] = []
            for od in ods:
                if not isinstance(od, dict):
                    continue
                od_cd = od.get("class_derivations", {})
                if isinstance(od_cd, dict):
                    for name, body in od_cd.items():
                        entry = body if isinstance(body, dict) else {}
                        entry.setdefault("name", name)
                        flattened.append(entry)
                elif isinstance(od_cd, list):
                    flattened.extend(od_cd)
            sd["class_derivations"] = flattened
            del sd["object_derivations"]
        for ncd in _iter_values_or_list(sd.get("class_derivations")):
            _flatten_ods_in_class_deriv(ncd)


def _inherit_populated_from(obj: dict[str, Any]) -> None:
    """Propagate ``populated_from`` from parent class down to nested CDs.

    Walks each class_derivation's slot_derivations.class_derivations; if
    a nested CD doesn't set ``populated_from``, it inherits from the
    outer class's value. Recurses through arbitrarily deep nesting.
    """
    for cd in _iter_values_or_list(obj.get("class_derivations")):
        _inherit_pf_in_slots(cd.get("slot_derivations"), cd.get("populated_from"))


def _inherit_pf_in_slots(slots: Any, parent_pf: str | None) -> None:
    """Recursively inherit populated_from into nested class_derivations."""
    for sd in _iter_values_or_list(slots):
        for ncd in _iter_values_or_list(sd.get("class_derivations")):
            if not ncd.get("populated_from") and parent_pf:
                ncd["populated_from"] = parent_pf
            _inherit_pf_in_slots(ncd.get("slot_derivations"), ncd.get("populated_from"))


def _iter_pv_derivations(obj: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield each PermissibleValueDerivation dict in ``obj`` for in-place mutation."""
    eds = obj.get("enum_derivations")
    if isinstance(eds, dict):
        ed_iter: Any = eds.values()
    elif isinstance(eds, list):
        ed_iter = eds
    else:
        return
    for ed in ed_iter:
        if not isinstance(ed, dict):
            continue
        pvds = ed.get("permissible_value_derivations")
        if isinstance(pvds, dict):
            pvd_iter: Any = pvds.values()
        elif isinstance(pvds, list):
            pvd_iter = pvds
        else:
            continue
        for pvd in pvd_iter:
            if isinstance(pvd, dict):
                yield pvd


def _coerce_pv_populated_from_to_list(obj: dict[str, Any]) -> None:
    """Coerce ``populated_from`` to a list on each PV deriv.

    Input shapes handled:

    * Scalar string: wrapped to a one-element list (user convenience that
      pydantic would otherwise reject for a multivalued field).
    * Explicit ``None`` or a list whose every element is ``None``
      (``populated_from:`` with no YAML value, possibly already wrapped to
      ``[None]`` by ``ReferenceValidator``): the key is removed so pydantic
      uses the ``default_factory=list`` default — treats "explicitly set to
      nothing" as "unset". Empty strings and other falsy-but-not-None
      values are kept (a user may legitimately map to the empty-string PV).
    * List: left as-is.
    """
    for pvd in _iter_pv_derivations(obj):
        if "populated_from" not in pvd:
            continue
        pf = pvd["populated_from"]
        if pf is None or (isinstance(pf, list) and all(x is None for x in pf)):
            del pvd["populated_from"]
        elif isinstance(pf, str):
            pvd["populated_from"] = [pf]


def _migrate_pv_sources_to_populated_from(obj: dict[str, Any]) -> None:
    """Move deprecated ``sources`` into ``populated_from`` on PV derivs.

    Applied after the pre-normalize scan has already detected and reported
    any ``sources`` usage and any ``sources`` + ``populated_from`` conflicts.
    For each PV deriv with ``sources`` set, copies into ``populated_from``
    (if not already set) and clears the ``sources`` key. A scalar string
    is wrapped to a one-element list rather than exploded into characters
    (defends against ``sources: "light_red"`` typos). Post-condition: no
    PV has ``sources`` set. The runtime can therefore rely on
    ``populated_from`` as the single source of truth and ignore ``sources``.
    """
    for pvd in _iter_pv_derivations(obj):
        srcs = pvd.pop("sources", None)
        if srcs and not pvd.get("populated_from"):
            pvd["populated_from"] = [srcs] if isinstance(srcs, str) else list(srcs)


def _coerce_schema_refs(obj: dict[str, Any]) -> None:
    """Coerce bare-string ``source_schema``/``target_schema`` to object form.

    The original spec form was a bare string (e.g. ``source_schema: my.yaml``);
    the field now ranges over ``SchemaReference``. For backward compatibility
    a string is rewritten to ``{"name": <string>}`` so legacy specs keep
    loading. The pre-normalize scan reports the string form as deprecated.
    """
    for schema_field in ("source_schema", "target_schema"):
        val = obj.get(schema_field)
        if isinstance(val, str):
            obj[schema_field] = {"name": val}
