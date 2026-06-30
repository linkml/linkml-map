"""Single source of truth for where expressions live in a transformation spec.

Cross-table references (``{Table.col}``) can appear in *any* expression, not
just ``SlotDerivation.expr`` — also enum/permissible-value ``expr`` and the
``expression*`` mapping tables inherited from ``ElementDerivation``. The join
normalizer must scan every one of these to synthesize the implicit joins they
imply, so this module enumerates them in one place.

The companion completeness-guard test introspects the transformer model and
fails if a new expression-bearing field is added without being registered here,
so the normalizer can never silently miss a join again.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

#: Fields whose value *is* an expression string (model range: ``string``).
#: Present on SlotDerivation, EnumDerivation, and PermissibleValueDerivation.
SELF_EXPR_FIELDS: tuple[str, ...] = ("expr",)

#: ``KeyVal`` mapping fields (inherited from ElementDerivation) and where the
#: expression(s) live within each entry:
#: ``"keys"`` — the mapping key is a (boolean) expression;
#: ``"values"`` — the entry value is an expression;
#: ``"both"`` — key and value are expressions.
MAPPING_EXPR_FIELDS: dict[str, str] = {
    "expression_mappings": "values",
    "expression_to_value_mappings": "keys",
    "expression_to_expression_mappings": "both",
}


def iter_expressions(derivation: Any) -> Iterator[str]:  # noqa: ANN401 - any *Derivation pydantic object
    """Yield every expression string carried directly by *derivation*.

    Covers ``expr`` and the ``expression*`` mapping fields. Does **not** recurse
    into nested derivations — callers walk the derivation tree and call this per
    node. Empty/absent fields yield nothing.

    :param derivation: a ``*Derivation`` object (Class/Slot/Enum/PermissibleValue).
    :yields: each non-empty expression string the derivation declares.
    """
    for field in SELF_EXPR_FIELDS:
        value = getattr(derivation, field, None)
        if value:
            yield value
    for field, where in MAPPING_EXPR_FIELDS.items():
        mapping = getattr(derivation, field, None) or {}
        for key, entry in mapping.items():
            if where in ("keys", "both") and key:
                yield key
            if where in ("values", "both"):
                entry_value = getattr(entry, "value", None)
                if entry_value:
                    yield entry_value
