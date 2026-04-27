"""
Restricted expression evaluator for LinkML transformation expressions.

Built on `simpleeval <https://github.com/danthedeckie/simpleeval>`_, with
LinkML-specific extensions:

- SQL-style NULL propagation: None flows through arithmetic, ordering
  comparisons, membership tests, and function calls (returning None).
  Equality (``==``, ``!=``) uses Python's native None handling
  (``None == "x"`` is ``False``).  Both ``{x}`` and bare ``x`` resolve
  identically.
- Distribution over collections: ``container.persons.name`` returns a list
  of names when ``persons`` is a list.
- Accepts any ``collections.abc.Mapping`` as variable bindings (for lazy resolution).

The long-term goal is to upstream the core evaluator into linkml-runtime.
See: https://github.com/linkml/linkml-map/issues/98
"""

import ast
import logging
import math
import uuid
from collections.abc import Mapping
from typing import Any

from simpleeval import EvalWithCompoundTypes, NameNotDefined

logger = logging.getLogger(__name__)


def eval_conditional(*conds: tuple[bool, Any]) -> Any:  # noqa: ANN401
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


def _try_numeric(value: Any) -> Any:  # noqa: ANN401
    """Attempt to coerce a value to a numeric type.

    Returns the value as-is if already numeric (int/float, not bool),
    coerces numeric strings to float, and returns None for anything else.

    >>> _try_numeric(5)
    5
    >>> _try_numeric(3.14)
    3.14
    >>> _try_numeric("3.14")
    3.14
    >>> _try_numeric("abc")
    >>> _try_numeric(None)
    >>> _try_numeric(True)
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _is_numeric(value: Any) -> bool:  # noqa: ANN401
    """
    Check whether a value can be converted to float.

    >>> _is_numeric("3.14")
    True
    >>> _is_numeric("abc")
    False
    >>> _is_numeric(5)
    True
    >>> _is_numeric("")
    False
    >>> _is_numeric(None)
    False
    >>> _is_numeric(True)
    False

    :param value: The value to check.
    :return: True if float(value) would succeed, False otherwise.
    """
    return _try_numeric(value) is not None


def _null_safe(func):  # noqa: ANN001, ANN202
    """Wrap a function to return None if any argument is None."""

    def wrapper(*args: Any) -> Any:  # noqa: ANN401
        if any(a is None for a in args):
            return None
        return func(*args)

    wrapper.__name__ = func.__name__
    return wrapper


def _distributing(func):  # noqa: ANN001, ANN202
    """Wrap a scalar function so it distributes over lists and propagates None."""

    def wrapper(*args: Any) -> Any:  # noqa: ANN401
        if args and isinstance(args[0], list):
            tail = args[1:]
            return [_null_safe(func)(x, *tail) for x in args[0]]
        if any(a is None for a in args):
            return None
        return func(*args)

    wrapper.__name__ = func.__name__
    return wrapper


def _list_reversed(x: list) -> list:
    """Return a reversed copy of a list."""
    return list(reversed(x))


def _first(x: list) -> Any:  # noqa: ANN401
    """Return the first element of a list, or None if empty.

    >>> _first([10, 20, 30])
    10
    >>> _first([]) is None
    True
    """
    return x[0] if x else None


def _last(x: list) -> Any:  # noqa: ANN401
    """Return the last element of a list, or None if empty.

    >>> _last([10, 20, 30])
    30
    >>> _last([]) is None
    True
    """
    return x[-1] if x else None


#: Functions that accept a list as their first argument (no distribution).
_LIST_FUNCTIONS: dict[str, Any] = {
    "max": _null_safe(max),
    "min": _null_safe(min),
    "len": _null_safe(len),
    "sum": _null_safe(sum),
    "sorted": _null_safe(sorted),
    "any": _null_safe(any),
    "all": _null_safe(all),
    "reversed": _null_safe(_list_reversed),
    "first": _null_safe(_first),
    "last": _null_safe(_last),
}

def _substr(s: str, start: int, end: int | None = None) -> str:
    """Extract a substring by position.

    >>> _substr("hello", 1, 3)
    'el'
    >>> _substr("hello", 2)
    'llo'
    """
    return s[start:end]


#: Functions that operate on scalars and should distribute over lists.
_SCALAR_FUNCTIONS: dict[str, Any] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "strlen": len,
    "uuid5": _uuid5,
    "substr": _substr,
    # String case/formatting
    "upper": str.upper,
    "lower": str.lower,
    "title": str.title,
    "capitalize": str.capitalize,
    # Whitespace trimming
    "strip": str.strip,
    "lstrip": str.lstrip,
    "rstrip": str.rstrip,
    # String content
    "replace": str.replace,
    "startswith": str.startswith,
    "endswith": str.endswith,
    "contains": str.__contains__,
    # String splitting/joining
    "split": str.split,
    "join": str.join,
}


def _is_str(value: Any) -> bool:  # noqa: ANN401
    """Check whether a value is a string."""
    return isinstance(value, str)


def _is_int(value: Any) -> bool:  # noqa: ANN401
    """Check whether a value is an integer (excludes bools)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_float(value: Any) -> bool:  # noqa: ANN401
    """Check whether a value is a float."""
    return isinstance(value, float)


def _is_bool(value: Any) -> bool:  # noqa: ANN401
    """Check whether a value is a boolean."""
    return isinstance(value, bool)


def _is_list(value: Any) -> bool:  # noqa: ANN401
    """Check whether a value is a list."""
    return isinstance(value, list)


def _coalesce(*args: Any) -> Any:  # noqa: ANN401
    """Return the first non-None argument, or None if all are None.

    >>> _coalesce(None, "fallback")
    'fallback'
    >>> _coalesce("hello", "fallback")
    'hello'
    >>> _coalesce(None, None, "last")
    'last'
    >>> _coalesce(None, None) is None
    True
    """
    for arg in args:
        if arg is not None:
            return arg
    return None


#: Type-testing predicates (not distributing — test the value as-is).
_TYPE_PREDICATES: dict[str, Any] = {
    "is_str": _is_str,
    "is_int": _is_int,
    "is_float": _is_float,
    "is_bool": _is_bool,
    "is_list": _is_list,
}

#: All built-in functions available in expressions.
FUNCTIONS: dict[str, Any] = {
    **_LIST_FUNCTIONS,
    **{name: _distributing(func) for name, func in _SCALAR_FUNCTIONS.items()},
    **_TYPE_PREDICATES,
    "case": eval_conditional,
    "coalesce": _coalesce,
    "is_numeric": _is_numeric,
}


def _maybe_coerce_numeric(left: Any, right: Any) -> tuple[Any, Any]:  # noqa: ANN401
    """
    Coerce a numeric-string operand to match the other operand's numeric type.

    If both operands are already the same type, or neither is a numeric/string
    mismatch, return them unchanged.

    >>> _maybe_coerce_numeric(1, '1')
    (1, 1)
    >>> _maybe_coerce_numeric('3.14', 3.14)
    (3.14, 3.14)
    >>> _maybe_coerce_numeric(1, 'abc')
    (1, 'abc')
    >>> _maybe_coerce_numeric('a', 'b')
    ('a', 'b')
    >>> _maybe_coerce_numeric(True, '0')
    (True, '0')
    """
    if type(left) is type(right):
        return left, right
    if isinstance(left, int | float) and not isinstance(left, bool) and isinstance(right, str):
        try:
            return left, type(left)(right)
        except (ValueError, TypeError):
            return left, right
    if isinstance(right, int | float) and not isinstance(right, bool) and isinstance(left, str):
        try:
            return type(right)(left), right
        except (ValueError, TypeError):
            return left, right
    return left, right


def _null_propagating(op):  # noqa: ANN001, ANN202
    """Wrap a binary operator with null propagation and numeric coercion fallback.

    Handles four cases:
    - Either operand is None → None (null propagation)
    - Operation succeeds natively → return result (e.g. str + str is concat)
    - Operation fails but operands are numeric strings → coerce to float and retry
    - Operands can't be made numeric → None with warning (enables case() guards)

    Note: ``+`` on two strings succeeds natively as concatenation and is not
    coerced. Use ``x + 0 + y`` or explicit ``float()`` if numeric addition of
    string values is needed.
    """

    def wrapper(left: Any, right: Any) -> Any:  # noqa: ANN401
        if left is None or right is None:
            return None
        try:
            return op(left, right)
        except (TypeError, ValueError):
            left_n, right_n = _try_numeric(left), _try_numeric(right)
            if left_n is None or right_n is None:
                logger.warning(f"Non-numeric operand in {op.__name__}: {left!r}, {right!r}; returning None")
                return None
            return op(left_n, right_n)

    return wrapper


def _null_propagating_unary(op):  # noqa: ANN001, ANN202
    """Wrap a unary operator to return None if the operand is None."""

    def wrapper(operand: Any) -> Any:  # noqa: ANN401
        if operand is None:
            return None
        return op(operand)

    return wrapper


def _coercing(op):  # noqa: ANN001, ANN202
    """Wrap a comparison operator to coerce numeric strings before comparing."""

    def wrapper(left: Any, right: Any) -> Any:  # noqa: ANN401
        left, right = _maybe_coerce_numeric(left, right)
        return op(left, right)

    return wrapper


class LinkMLEvaluator(EvalWithCompoundTypes):
    """
    Expression evaluator with LinkML-specific extensions.

    Extends ``simpleeval.EvalWithCompoundTypes`` with:

    - SQL-style NULL propagation for arithmetic, ordering comparisons,
      membership tests, and function calls
    - Distribution over lists/dicts on attribute access
    - Numeric-string coercion for comparison operators
    """

    def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(**kwargs)
        for op_type in (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE):
            self.operators[op_type] = _coercing(self.operators[op_type])
        for op_type in (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn):
            self.operators[op_type] = _null_propagating(self.operators[op_type])
        for op_type in (
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.LShift,
            ast.RShift,
            ast.BitXor,
            ast.BitOr,
            ast.BitAnd,
        ):
            self.operators[op_type] = _null_propagating(self.operators[op_type])
        for op_type in (ast.USub, ast.UAdd, ast.Invert):
            self.operators[op_type] = _null_propagating_unary(self.operators[op_type])

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
        Override set evaluation for ``{x}`` variable reference syntax.

        In the LinkML expression language, ``{x}`` resolves the variable x.
        If x is None, None is returned (SQL-style null propagation).
        ``{x}`` and bare ``x`` are equivalent.
        """
        if len(node.elts) != 1:
            msg = "The {} must enclose a single variable"
            raise ValueError(msg)
        e = node.elts[0]
        if not isinstance(e, ast.Name | ast.Attribute):
            msg = "The {} must enclose a variable"
            raise TypeError(msg)
        return self._eval(e)

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
    >>> _distributed_getattr(P("Alice"), "_secret")
    Traceback (most recent call last):
        ...
    NameError: Access to private attribute '_secret' is not allowed
    """
    if attr.startswith("_"):
        msg = f"Access to private attribute {attr!r} is not allowed"
        raise NameError(msg)
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
    return evaluator.eval(expr)


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

    variables can be passed using ``{x}`` or bare ``x`` — both are equivalent

    >>> eval_expr('{x} + {y}', x=1, y=2)
    3
    >>> eval_expr('x + y', x=1, y=2)
    3

    Nulls:

    None propagates through arithmetic, ordering comparisons, membership
    tests, and function calls (SQL-style).  Equality (==, !=) uses Python's
    native None handling (None == "x" is False):

    >>> print(eval_expr('{x} + {y}', x=None, y=2))
    None
    >>> print(eval_expr('x + 1', x=None))
    None
    >>> print(eval_expr('x <= 0', x=None))
    None
    >>> print(eval_expr('float(x)', x=None))
    None

    case() branching works naturally with null values:

    >>> eval_expr('case((x == "1", "YES"), (True, "NO"))', x=None)
    'NO'
    >>> eval_expr('case(({x} == "1", "YES"), (True, "NO"))', x=None)
    'NO'

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
