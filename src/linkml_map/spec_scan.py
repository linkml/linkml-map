"""The SCAN phase: deprecated-field detection over a raw specification dict.

Runs between the SHAPE and MIGRATE phases of
:func:`linkml_map.spec_normalizer.normalize_spec`, so the dict it sees is
structurally canonical but still carries the user's original field values.

This module deliberately depends on nothing but the standard library:
:mod:`linkml_map.spec_normalizer` and :mod:`linkml_map.validator` both build
on it, so it has to sit at the bottom of that stack.
"""

from dataclasses import dataclass
from typing import Any, Literal


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


def iter_derivation_dicts(raw: Any) -> list[dict[str, Any]]:
    """Normalize a derivations section (dict or list) to a list of dicts.

    Assumes the SHAPE phase of
    :func:`linkml_map.spec_normalizer.normalize_spec` has already
    canonicalized compact-key list items, so callers only need to handle
    dict-keyed and explicit-name list forms here.
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

    Runs in the SCAN phase of
    :func:`linkml_map.spec_normalizer.normalize_spec` — after SHAPE (which
    runs ``ReferenceValidator.normalize()`` and the local compact-key
    pre-expansion) and before MIGRATE (which flattens
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

    for cd in iter_derivation_dicts(data.get("class_derivations")):
        cd_name = cd.get("name", "<unnamed>")
        if cd.get("sources"):
            sources_counts["ClassDerivation"].append(cd_name)
        for sd in iter_derivation_dicts(cd.get("slot_derivations")):
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

    for ed in iter_derivation_dicts(data.get("enum_derivations")):
        ed_name = ed.get("name", "<unnamed>")
        if ed.get("sources"):
            sources_counts["EnumDerivation"].append(ed_name)
        for pvd in iter_derivation_dicts(ed.get("permissible_value_derivations")):
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
