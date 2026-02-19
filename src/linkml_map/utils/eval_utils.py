"""
Restricted expression evaluator for LinkML transformation expressions.

Built on `simpleeval <https://github.com/danthedeckie/simpleeval>`_, with
LinkML-specific extensions:

- ``{x}`` null-propagation syntax: if any ``{var}`` resolves to None,
  the entire expression evaluates to None.
- Distribution over collections: ``container.persons.name`` returns a list
  of names when ``persons`` is a list.
- Accepts any ``collections.abc.Mapping`` as variable bindings (for lazy resolution).

The long-term goal is to upstream the core evaluator into linkml-runtime.
See: https://github.com/linkml/linkml-map/issues/98
"""

import ast
import uuid
from collections.abc import Mapping
from typing import Any

from simpleeval import EvalWithCompoundTypes, NameNotDefined


class UnsetValueError(Exception):
    """Raise when a required ``{variable}`` binding is None."""


def eval_conditional(*conds: list[tuple[bool, Any]]) -> Any:  # noqa: ANN401
    """
    Evaluate a conditional.

    Return the first value whose condition is true.

    >>> x = 10
    >>> eval_conditional((x < 25, 'low'), (x > 25, 'high'), (True, 'low'))
    'low'

    :param conds: conditionals to be evaluated
    :return: Any
    """
    for is_true, val in conds:
        if is_true:
            return val
    return None


def _uuid5(namespace: str, name: str) -> str:
    """
    Generate a deterministic UUID5 string from a namespace URL and a name.

    This function uses a two-level UUID5 generation strategy:

    1. First, it derives a namespace UUID by hashing the given ``namespace``
       string (which should be a URL, e.g. ``"https://example.org/ns"``)
       using :data:`uuid.NAMESPACE_URL`.
    2. Then, it computes the final UUID5 using that derived namespace UUID
       and the provided ``name`` string.

    Because UUID5 is fully deterministic, calling this function with the
    same ``namespace`` and ``name`` will always return the same UUID string.

    >>> ns = "https://example.org/ns"
    >>> _uuid5(ns, "example") == _uuid5(ns, "example")
    True
    >>> _uuid5(ns, "example") != _uuid5(ns, "different")
    True

    :param namespace: Namespace identifier as a URL string.
    :param name: Name string to be combined with the derived namespace UUID.
    :return: Deterministic UUID5 as a string.
    """
    ns = uuid.uuid5(uuid.NAMESPACE_URL, namespace)
    return str(uuid.uuid5(ns, name))


def _distributing(func):  # noqa: ANN001, ANN202
    """Wrap a scalar function so it distributes over list arguments."""

    def wrapper(*args: Any) -> Any:  # noqa: ANN401
        if args and isinstance(args[0], list):
            return [func(x, *args[1:]) for x in args[0]]
        return func(*args)

    wrapper.__name__ = func.__name__
    return wrapper


#: Functions that accept a list as their first argument (no distribution).
_LIST_FUNCTIONS: dict[str, Any] = {
    "max": max,
    "min": min,
    "len": len,
}

#: Functions that operate on scalars and should distribute over lists.
_SCALAR_FUNCTIONS: dict[str, Any] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "abs": abs,
    "round": round,
    "strlen": len,
    "uuid5": _uuid5,
}

#: All built-in functions available in expressions.
FUNCTIONS: dict[str, Any] = {
    **_LIST_FUNCTIONS,
    **{name: _distributing(func) for name, func in _SCALAR_FUNCTIONS.items()},
    "case": eval_conditional,
}


class LinkMLEvaluator(EvalWithCompoundTypes):
    """
    Expression evaluator with LinkML-specific extensions.

    Extends ``simpleeval.EvalWithCompoundTypes`` with:

    - Distribution over lists/dicts on attribute access
    - ``{x}`` null-propagation via overridden set evaluation
    """

    def _eval_name(self, node: ast.Name) -> Any:  # noqa: ANN401
        """
        Override name resolution to return None for unbound variables.

        The default simpleeval behavior raises ``NameNotDefined``.
        In LinkML expressions, unbound variables resolve to None.
        """
        try:
            return super()._eval_name(node)
        except NameNotDefined:
            return None

    def _eval_set(self, node: ast.Set) -> Any:  # noqa: ANN401
        """
        Override set evaluation for ``{x}`` null-propagation syntax.

        In the LinkML expression language, ``{x}`` is not a set literal —
        it means "resolve x, but if x is None, abort the entire expression."
        """
        if len(node.elts) != 1:
            msg = "The {} must enclose a single variable"
            raise ValueError(msg)
        e = node.elts[0]
        if not isinstance(e, ast.Name):
            msg = "The {} must enclose a variable"
            raise TypeError(msg)
        v = self._eval(e)
        if v is None:
            msg = f"{e.id} is not set"
            raise UnsetValueError(msg)
        return v

    def _eval_attribute(self, node: ast.Attribute) -> Any:  # noqa: ANN401
        """
        Override attribute access to distribute over collections.

        If the object is a list, ``obj.attr`` returns ``[item.attr for item in obj]``.
        If the object is a dict, it distributes over values.
        """
        obj = self._eval(node.value)
        return _distributed_getattr(obj, node.attr)


def _distributed_getattr(obj: Any, attr: str) -> Any:  # noqa: ANN401
    """
    Look up an attribute, distributing over lists and dicts.

    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class P:
    ...     name: str
    >>> _distributed_getattr([P("Alice"), P("Bob")], "name")
    ['Alice', 'Bob']
    >>> _distributed_getattr(None, "name") is None
    True
    """
    if isinstance(obj, list):
        return [_distributed_getattr(item, attr) for item in obj]
    if isinstance(obj, dict):
        return [_distributed_getattr(v, attr) for v in obj.values()]
    if obj is None:
        return None
    return getattr(obj, attr)


def _make_evaluator(names: Any, functions: Any = None) -> LinkMLEvaluator:  # noqa: ANN401
    """Create a configured LinkMLEvaluator instance."""
    return LinkMLEvaluator(names=names, functions=functions or FUNCTIONS)


def eval_expr_with_mapping(expr: str, mapping: Mapping) -> Any:  # noqa: ANN401
    """
    Evaluate a given expression, with restricted syntax.

    This function is equivalent to eval_expr where ``**kwargs`` has been
    switched to a Mapping (e.g. a dictionary). See eval_expr for details.
    """
    if expr == "None":
        return None
    evaluator = _make_evaluator(names=mapping)
    try:
        return evaluator.eval(expr)
    except UnsetValueError:
        return None


def eval_expr(expr: str, **kwargs: Any) -> Any:  # noqa: ANN401
    """
    Evaluate a given expression, with restricted syntax.

    Arithmetic:

    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    >>> eval_expr('10 % 3')
    1
    >>> eval_expr('7 // 2')
    3

    Variables:

    variables can be passed

    >>> eval_expr('{x} + {y}', x=1, y=2)
    3

    Nulls:

    - If a variable is enclosed in {}s then entire expression will eval to None if variable is unset

    >>> print(eval_expr('{x} + {y}', x=None, y=2))
    None

    Comparisons:

    >>> eval_expr('1 != 2')
    True
    >>> eval_expr('1 != 1')
    False
    >>> eval_expr('"a" in "abc"')
    True
    >>> eval_expr('1 not in [2, 3]')
    True

    Logical operators:

    >>> eval_expr('True and False')
    False
    >>> eval_expr('True or False')
    True
    >>> eval_expr('not True')
    False

    Functions:

    - only a small set of functions are currently supported

    >>> eval_expr('strlen("a" + "bc")')
    3
    >>> eval_expr('abs(-5)')
    5
    >>> eval_expr('int("42")')
    42

    Paths:

    - Expressions such as ``person.name`` can be used on objects to lookup by attribute/slot
    - Paths can be chained, e.g. ``person.address.street``
    - Operations on lists are distributed, e.g ``container.persons.name`` will return a list of names
    - Similarly ``strlen(container.persons.name)`` will return a list whose members are the lengths of all names

    :param expr: expression to evaluate
    :param kwargs: variable bindings
    """
    return eval_expr_with_mapping(expr, kwargs)
