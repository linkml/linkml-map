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

import ast
from collections.abc import Iterable, Iterator
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


def extract_braced_reference_roots(expression: str) -> set[str]:
    """Return the bare-name roots of braced ``{Name.attr}`` references.

    Only braced references (``ast.Set`` single-element displays — the LinkML
    expression reference syntax, mirroring ``_eval_set``) are inspected, so
    lambda parameters, comprehension targets, and raw-Python attribute access in
    unrestricted expressions are *not* treated as references. Each braced
    ``{x.y}`` contributes its root ``x``; a bare ``{col}`` contributes nothing.

    Used to spot a reference whose root is neither a known table, an in-scope
    source, a source slot, nor a function — an unresolvable ``{Unknown.col}``
    that would otherwise silently null at runtime.

    :param expression: a LinkML expression string.
    :returns: the set of braced-reference attribute roots.
    :raises SyntaxError: if *expression* is not parseable.
    """
    roots: set[str] = set()
    tree = ast.parse(expression, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, ast.Set):
            for elt in node.elts:
                if isinstance(elt, ast.Attribute) and isinstance(elt.value, ast.Name):
                    roots.add(elt.value.id)
    return roots


def extract_table_references(expression: str, table_names: Iterable[str]) -> set[str]:
    """Return the tables referenced as ``{Table.col}`` in an expression.

    The LinkML expression language is parsed with Python's ``ast``, so
    ``{Table.col}`` appears as attribute access ``Table.col``. A reference counts
    only when the attribute's root is a bare name matching a known table (a
    source-schema class); bare column names (``{col}``) and attribute access on
    non-tables are ignored. Parsing uses ``exec`` mode because the expression
    language permits statements (assignments, comprehensions) that ``eval`` mode
    rejects.

    :param expression: a LinkML expression string.
    :param table_names: names that denote tables (source-schema classes).
    :returns: the set of referenced table names.
    :raises SyntaxError: if *expression* is not parseable (a malformed expr that
        would also fail at evaluation — surfaced here rather than masked).
    """
    tables = set(table_names)
    refs: set[str] = set()
    tree = ast.parse(expression, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in tables:
            refs.add(node.value.id)
    return refs
