"""Tests for the restricted expression evaluator."""

# ruff: noqa: ANN401, PLR2004

import re
from dataclasses import dataclass, field
from typing import Any, Optional

import pytest

from linkml_map.utils.eval_utils import (
    _evaluator_pool,
    _parse_cached,
    _uuid5,
    eval_expr,
    eval_expr_with_mapping,
)

# -- helpers for path / attribute tests --


@dataclass
class Person:
    """Simple person dataclass for testing attribute access."""

    name: str = ""
    age: int = 0
    address: Optional["Address"] = None


@dataclass
class Address:
    """Simple address dataclass for testing chained attribute access."""

    street: str = ""


@dataclass
class Container:
    """Container with list and dict fields for distribution tests."""

    persons: list = field(default_factory=list)
    person_index: dict = field(default_factory=dict)


UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


# ---- Arithmetic operators ----


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("1 + 2", 3),
        ("5 - 3", 2),
        ("3 * 4", 12),
        ("10 / 4", 2.5),
        ("7 // 2", 3),
        ("10 % 3", 1),
        ("2**6", 64),
        ("2^6", 4),
        ("-5", -5),
        ("1 + 2*3**(4^5) / (6 + -7)", -5.0),
        ("'x' + 'y'", "xy"),
        ("['a','b'] + ['c','d']", ["a", "b", "c", "d"]),
    ],
    ids=[
        "add",
        "sub",
        "mul",
        "div",
        "floordiv",
        "mod",
        "pow",
        "xor",
        "neg",
        "precedence",
        "str_concat",
        "list_concat",
    ],
)
def test_arithmetic(expr: str, expected: Any) -> None:
    """Test arithmetic operators and precedence."""
    assert eval_expr(expr) == expected


# ---- Comparison operators ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ("1 + 1 == 2", {}, True),
        ("1 != 2", {}, True),
        ("1 != 1", {}, False),
        ("1 < 2", {}, True),
        ("2 < 1", {}, False),
        ("1 <= 1", {}, True),
        ("2 <= 1", {}, False),
        ("2 > 1", {}, True),
        ("1 > 2", {}, False),
        ("1 >= 1", {}, True),
        ("0 >= 1", {}, False),
        ("x is None", {"x": None}, True),
        ("x is None", {"x": 1}, False),
        ("x is not None", {"x": 1}, True),
        ("x is not None", {"x": None}, False),
        ('"a" in "abc"', {}, True),
        ('"z" in "abc"', {}, False),
        ("1 not in [2, 3]", {}, True),
        ("1 not in [1, 2]", {}, False),
        ("x in items", {"x": 2, "items": [1, 2, 3]}, True),
        ("x in items", {"x": 5, "items": [1, 2, 3]}, False),
        ("1 < 2 < 3", {}, True),
        ("1 < 2 > 3", {}, False),
        ("1 <= 1 < 2", {}, True),
    ],
    ids=[
        "eq",
        "ne_true",
        "ne_false",
        "lt_true",
        "lt_false",
        "le_true",
        "le_false",
        "gt_true",
        "gt_false",
        "ge_true",
        "ge_false",
        "is_none",
        "is_not_none",
        "is_not_none_true",
        "is_not_none_false",
        "in_str_true",
        "in_str_false",
        "not_in_true",
        "not_in_false",
        "in_list_true",
        "in_list_false",
        "chained_lt_lt",
        "chained_lt_gt",
        "chained_le_lt",
    ],
)
def test_comparisons(expr: str, kwargs: dict, expected: bool) -> None:  # noqa: FBT001
    """Test comparison operators including chained comparisons."""
    assert eval_expr(expr, **kwargs) is expected


# ---- Logical operators ----


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("True and True", True),
        ("True and False", False),
        ("False or True", True),
        ("False or False", False),
        ("not True", False),
        ("not False", True),
        ("True and not False", True),
        ("not True or False", False),
        ("True and True and True", True),
        ("True and False and True", False),
        ("False or False or True", True),
        ("False or False or False", False),
    ],
    ids=[
        "and_tt",
        "and_tf",
        "or_ft",
        "or_ff",
        "not_t",
        "not_f",
        "and_not",
        "not_or",
        "multi_and_t",
        "multi_and_f",
        "multi_or_t",
        "multi_or_f",
    ],
)
def test_logical_operators(expr: str, expected: bool) -> None:  # noqa: FBT001
    """Test and, or, not operators."""
    assert eval_expr(expr) is expected


def test_and_short_circuit() -> None:
    """``and`` returns the first falsy value (short-circuit)."""
    assert eval_expr("0 and 1") == 0
    assert eval_expr("1 and 2") == 2


def test_or_short_circuit() -> None:
    """``or`` returns the first truthy value (short-circuit)."""
    assert eval_expr("0 or 2") == 2
    assert eval_expr("1 or 2") == 1


# ---- Variables and null propagation ----


def test_bare_variable() -> None:
    """Bare variable names resolve from bindings."""
    assert eval_expr("x", x="a") == "a"


def test_bare_variable_arithmetic() -> None:
    """Bare variables work in arithmetic expressions."""
    assert eval_expr("x+y", x=1, y=2) == 3


def test_curly_variable() -> None:
    """Curly-braced variables resolve from bindings."""
    assert eval_expr("{x} + {y}", x=1, y=2) == 3


def test_null_propagation() -> None:
    """None propagates through arithmetic: {x} + {y} returns None if either is None."""
    assert eval_expr("{x} + {y}", x=None, y=2) is None


def test_null_propagation_both_none() -> None:
    """None propagates through arithmetic when all variables are None."""
    assert eval_expr("{x} + {y}", x=None, y=None) is None


def test_bare_null_propagation() -> None:
    """Bare variables propagate None through arithmetic, same as {x}."""
    assert eval_expr("x + 1", x=None) is None
    assert eval_expr("x + y", x=None, y=2) is None
    assert eval_expr("x + y", x=1, y=None) is None


def test_null_in_conditional() -> None:
    """None values work in conditionals and case() branching."""
    assert eval_expr("'NOT_NULL' if x else 'NULL'", x=None) == "NULL"
    assert eval_expr("'NOT_NULL' if x else 'NULL'", x=1) == "NOT_NULL"
    assert eval_expr('case((x == "1", "YES"), (True, "NO"))', x=None) == "NO"
    assert eval_expr('case(({x} == "1", "YES"), (True, "NO"))', x=None) == "NO"


def test_null_in_ordering_comparison() -> None:
    """None propagates through ordering comparisons (<, <=, >, >=)."""
    assert eval_expr("x <= 0", x=None) is None
    assert eval_expr("x > 5", x=None) is None
    assert eval_expr("x < 100", x=None) is None
    assert eval_expr("x >= 0", x=None) is None
    assert eval_expr("{x} <= 0", x=None) is None
    # Eq/NotEq still use Python's native None handling
    assert eval_expr("x == 1", x=None) is False
    assert eval_expr("x != 1", x=None) is True


def test_null_in_membership() -> None:
    """None propagates through in/not-in when either operand is None."""
    assert eval_expr("x in [1, 2, 3]", x=None) is None
    assert eval_expr("x not in [1, 2, 3]", x=None) is None
    assert eval_expr("1 in x", x=None) is None
    assert eval_expr("1 not in x", x=None) is None
    # Non-None cases still work normally
    assert eval_expr("1 in [1, 2, 3]") is True
    assert eval_expr("4 not in [1, 2, 3]") is True


def test_null_in_numeric_guard_pattern() -> None:
    """The common dm-bip pattern case(({x} <= 0, None), (True, ...)) works with null input."""
    assert eval_expr("case(({x} <= 0, None), (True, {x} * 2.54))", x=None) is None
    assert eval_expr("case(({x} <= 0, None), (True, {x} * 2.54))", x=65) == 165.1
    assert eval_expr("case(({x} <= 0, None), (True, {x} * 2.54))", x=0) is None


def test_is_numeric() -> None:
    """is_numeric() checks whether a value can be converted to float."""
    assert eval_expr("is_numeric(x)", x="3.14") is True
    assert eval_expr("is_numeric(x)", x="abc") is False
    assert eval_expr("is_numeric(x)", x=5) is True
    assert eval_expr("is_numeric(x)", x="") is False
    assert eval_expr("is_numeric(x)", x=None) is False
    assert eval_expr("is_numeric(x)", x="0") is True


def test_is_numeric_guard_pattern() -> None:
    """is_numeric() enables guarded numeric branching in case() expressions."""
    expr = "case((is_numeric(x), x * 2.54), (True, None))"
    assert eval_expr(expr, x="5") == 12.7
    assert eval_expr(expr, x="abc") is None
    assert eval_expr(expr, x="") is None
    assert eval_expr(expr, x=None) is None


def test_arithmetic_coerces_numeric_strings() -> None:
    """Arithmetic operators coerce numeric strings to float."""
    assert eval_expr("x / y * 10", x="100", y="50") == 20.0
    assert eval_expr("{x} / 100.0 * {y}", x="200", y="50") == 100.0


def test_arithmetic_multiply_numeric_string_is_numeric() -> None:
    """``*`` on a numeric string is arithmetic, not Python string repetition (#285).

    A numeric-looking column typed ``string`` (so the loader leaves it a string)
    must not turn ``{col} * 365`` into the string repeated 365 times. Coercion
    preserves the other operand's type, so the result matches the int-typed path.
    """
    assert eval_expr("{col} * 365", col="71") == 25915
    assert eval_expr("{col} * 365", col=71) == 25915
    assert eval_expr("({col} * 365) + 1825", col="71") == 27740
    assert eval_expr("{col} * 365", col="3.14") == pytest.approx(1146.1)
    # int * str is native repetition too, so the RHS path needs the same guard.
    assert eval_expr("365 * {col}", col="71") == 25915
    assert eval_expr("365 * {col}", col="3.14") == pytest.approx(1146.1)


def test_arithmetic_multiply_string_and_number_preserves_concatenation_and_lists() -> None:
    """``*`` stays numeric for number/string pairs but keeps genuine string/list semantics."""
    # Two strings still concatenate with + (documented behavior), not coerced.
    assert eval_expr("{a} + {b}", a="foo", b="bar") == "foobar"
    assert eval_expr("{a} + {b}", a="71", b="365") == "71365"
    # A list times a number is genuine repetition/distribution, left untouched.
    assert eval_expr("x * 3", x=[1, 2]) == [1, 2, 1, 2, 1, 2]


def test_arithmetic_non_numeric_string_returns_none() -> None:
    """Non-numeric strings in arithmetic return None with a warning instead of crashing."""
    assert eval_expr("x / y", x="100", y="abc") is None
    assert eval_expr("x * y", x="abc", y="10") is None
    assert eval_expr("x + y", x="abc", y=10) is None
    # ``*`` is the trap: str * int succeeds natively as repetition, so a
    # non-numeric string times a number must be forced to None, not "abcabc...".
    assert eval_expr("x * y", x="abc", y=10) is None
    assert eval_expr("x * y", x=10, y="abc") is None


def test_null_in_function_call() -> None:
    """None propagates through function calls."""
    assert eval_expr("float(x)", x=None) is None
    assert eval_expr("strlen(x)", x=None) is None
    assert eval_expr("abs(x)", x=None) is None


def test_unbound_variable() -> None:
    """An unbound variable resolves to None."""
    assert eval_expr("x") is None


def test_none_expression_literal() -> None:
    """The literal string 'None' evaluates to None."""
    assert eval_expr("None") is None


def test_list_variable_concatenation() -> None:
    """List variables can be concatenated."""
    assert eval_expr("{x} + {y}", x=["a", "b"], y=["c", "d"]) == ["a", "b", "c", "d"]


# ---- Curly-braced attribute access (cross-table syntax) ----


def test_curly_attribute_access() -> None:
    """{obj.attr} resolves attribute access with null propagation."""
    from linkml_map.utils.dynamic_object import DynObj

    demo = DynObj(age=30, name="Alice")
    assert eval_expr("{demo.age} * 365", demo=demo) == 30 * 365


def test_curly_attribute_null_propagation_none_obj() -> None:
    """{obj.attr} propagates None when the object itself is None."""
    assert eval_expr("{demo.age} * 365", demo=None) is None


def test_curly_attribute_null_propagation_missing_attr() -> None:
    """{obj.attr} propagates None when the attribute is missing."""
    from linkml_map.utils.dynamic_object import DynObj

    demo = DynObj(name="Alice")  # no 'age' attribute
    assert eval_expr("{demo.age} * 365", demo=demo) is None


def test_curly_attribute_in_string_concat() -> None:
    """{obj.attr} works in string concatenation expressions."""
    from linkml_map.utils.dynamic_object import DynObj

    demo = DynObj(prefix="Dr")
    assert eval_expr("{demo.prefix} + '. Smith'", demo=demo) == "Dr. Smith"


# ---- Functions ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ("max([1, 5, 2])", {}, 5),
        ("max({x})", {"x": [1, 5, 2]}, 5),
        ("min([3, 1, 2])", {}, 1),
        ("len([1, 2, 3])", {}, 3),
        ('strlen("abc")', {}, 3),
        ('strlen("a" + "bc")', {}, 3),
        ("str(42)", {}, "42"),
        ('int("42")', {}, 42),
        ('float("3.14")', {}, 3.14),
        ("bool(1)", {}, True),
        ("bool(0)", {}, False),
        ("abs(-5)", {}, 5),
        ("round(3.7)", {}, 4),
    ],
    ids=[
        "max",
        "max_var",
        "min",
        "len",
        "strlen",
        "strlen_concat",
        "str",
        "int",
        "float",
        "bool_true",
        "bool_false",
        "abs",
        "round",
    ],
)
def test_functions(expr: str, kwargs: dict, expected: Any) -> None:
    """Test built-in functions."""
    assert eval_expr(expr, **kwargs) == expected


def test_case_function() -> None:
    """Test the case() conditional function."""
    case = "case(({x} < 25, 'LOW'), ({x} > 75, 'HIGH'), (True, 'MEDIUM'))"
    assert eval_expr(case, x=10) == "LOW"
    assert eval_expr(case, x=100) == "HIGH"
    assert eval_expr(case, x=50) == "MEDIUM"


def test_function_distributes_over_lists() -> None:
    """Non-list functions distribute over list arguments."""
    assert eval_expr("strlen(items)", items=["ab", "cde", "f"]) == [2, 3, 1]


def test_unknown_function_raises() -> None:
    """Calling an unknown function raises an error with a helpful message."""
    with pytest.raises(Exception, match="Unknown function 'my_func'") as excinfo:
        eval_expr("my_func(1)")
    assert "--functions" in str(excinfo.value)


def test_unknown_underscore_function_omits_extensions_hint() -> None:
    """Names starting with ``_`` cannot be loaded via ``--functions``.

    The extension loader skips ``_``-prefixed names, so suggesting
    ``--functions`` would mislead the user. The error message stays minimal.
    """
    from linkml_map.utils.eval_utils import UnknownFunctionError

    with pytest.raises(UnknownFunctionError, match="Unknown function '_hidden'") as excinfo:
        eval_expr("_hidden(1)")
    assert "--functions" not in str(excinfo.value)


def test_import_call_reports_unsupported() -> None:
    """``__import__`` raises with an explicit unsupported-feature message."""
    from linkml_map.utils.eval_utils import UnknownFunctionError

    with pytest.raises(UnknownFunctionError, match="Import expressions are not supported") as excinfo:
        eval_expr("__import__('os')")
    assert "--functions" not in str(excinfo.value)


# ---- Conditionals ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ("'EQ' if {x} == {y} else 'NEQ'", {"x": 1, "y": 1}, "EQ"),
        ("'EQ' if {x} == {y} else 'NEQ'", {"x": 1, "y": 2}, "NEQ"),
        ("'yes' if x > 0 and x < 10 else 'no'", {"x": 5}, "yes"),
        ("'yes' if x > 0 and x < 10 else 'no'", {"x": 15}, "no"),
    ],
    ids=["ternary_eq", "ternary_neq", "ternary_and_true", "ternary_and_false"],
)
def test_ternary(expr: str, kwargs: dict, expected: str) -> None:
    """Test ternary (if/else) expressions."""
    assert eval_expr(expr, **kwargs) == expected


# ---- Data structures ----


def test_list_literal() -> None:
    """Test list literal evaluation."""
    assert eval_expr("['a', 'b', 'c']") == ["a", "b", "c"]


def test_tuple_literal() -> None:
    """Test tuple literal evaluation."""
    assert eval_expr("(1, 2, 3)") == (1, 2, 3)


def test_dict_literal() -> None:
    """Test dict literal evaluation."""
    assert eval_expr("{'a': 1}") == {"a": 1}


def test_subscript_dict() -> None:
    """Test subscript access on dicts."""
    assert eval_expr('x["a"] + y', x={"a": 1}, y=2) == 3


def test_subscript_nested() -> None:
    """Test nested subscript access."""
    assert eval_expr('x["a"]["b"] + y', x={"a": {"b": 1}}, y=2) == 3


def test_subscript_list() -> None:
    """Test subscript access on lists."""
    assert eval_expr("x[0]", x=[10, 20, 30]) == 10


# ---- Paths and attribute access ----


def test_simple_attribute() -> None:
    """Test dotted attribute access on objects."""
    p = Person(name="Alice", age=30)
    assert eval_expr("p.name", p=p) == "Alice"


def test_chained_attribute() -> None:
    """Test chained dotted attribute access."""
    p = Person(name="Alice", address=Address(street="1 Main St"))
    assert eval_expr("p.address.street", p=p) == "1 Main St"


def test_attribute_distributes_over_list() -> None:
    """Attribute access on a list distributes to each element."""
    p1 = Person(name="Alice")
    p2 = Person(name="Bob")
    c = Container(persons=[p1, p2])
    assert eval_expr("c.persons.name", c=c) == ["Alice", "Bob"]


def test_chained_attribute_distributes_over_list() -> None:
    """Chained attribute access distributes over nested lists."""
    p1 = Person(name="Alice", address=Address(street="1 Main"))
    p2 = Person(name="Bob", address=Address(street="2 Elm"))
    c = Container(persons=[p1, p2])
    assert eval_expr("c.persons.address.street", c=c) == ["1 Main", "2 Elm"]


def test_function_on_distributed_attribute() -> None:
    """Functions work on distributed attribute results."""
    p1 = Person(name="Alice", address=Address(street="1 Main"))
    p2 = Person(name="Bob", address=Address(street="2 Elm"))
    c = Container(persons=[p1, p2])
    assert eval_expr("strlen(c.persons.address.street)", c=c) == [6, 5]


def test_len_on_list_attribute() -> None:
    """len() works on list-valued attributes."""
    c = Container(persons=[Person(name="Alice")])
    assert eval_expr("len(c.persons)", c=c) == 1


def test_attribute_distributes_over_dict_values() -> None:
    """Attribute access on a dict distributes over values."""
    p1 = Person(name="Alice")
    p2 = Person(name="Bob")
    c = Container(person_index={"a": p1, "b": p2})
    assert eval_expr("c.person_index.name", c=c) == ["Alice", "Bob"]


def test_attribute_on_none() -> None:
    """Attribute access on None returns None."""
    assert eval_expr("x.name", x=None) is None


def test_dict_key_access_via_subscript() -> None:
    """For direct key lookup on a dict, use subscript notation."""
    pd = {"name": "Alice", "age": 30}
    assert eval_expr('p["name"]', p=pd) == "Alice"


# ---- Constants and literals ----


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("True", True),
        ("False", False),
        ("42", 42),
        ("3.14", 3.14),
        ('"hello"', "hello"),
    ],
    ids=["true", "false", "int", "float", "str"],
)
def test_constants(expr: str, expected: Any) -> None:
    """Test constant/literal evaluation."""
    assert eval_expr(expr) == expected


# ---- Error handling ----


def test_import_blocked() -> None:
    """Import expressions are not supported."""
    from simpleeval import InvalidExpression

    with pytest.raises(InvalidExpression, match="Import expressions are not supported"):
        eval_expr("__import__('os').listdir()")


def test_private_attribute_blocked() -> None:
    """Accessing private/dunder attributes is blocked."""
    p = Person(name="Alice")
    with pytest.raises(NameError, match="private attribute"):
        eval_expr("p.__class__", p=p)


def test_set_must_enclose_single_variable() -> None:
    """The {x} syntax requires exactly one variable."""
    with pytest.raises(ValueError, match="single variable"):
        eval_expr("{x, y}", x=1, y=2)


def test_set_must_enclose_name() -> None:
    """The {x} syntax requires a variable name, not an expression."""
    with pytest.raises(TypeError, match="must enclose a variable"):
        eval_expr("{1 + 2}")


def test_curly_braces_resolve_none() -> None:
    """{x} resolves to None when the variable is None (no exception)."""
    from linkml_map.utils.eval_utils import LinkMLEvaluator

    evaluator = LinkMLEvaluator(names={"x": None})
    assert evaluator.eval("{x}") is None


# ---- Mapping integration ----


def test_eval_expr_with_mapping_dict() -> None:
    """eval_expr_with_mapping works with a plain dict."""
    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    result = eval_expr_with_mapping("{x} + {y}", {"x": 1, "y": 2})
    assert result == 3


def test_eval_expr_with_mapping_custom_mapping() -> None:
    """eval_expr_with_mapping works with a custom Mapping (lazy resolution)."""
    from collections.abc import Mapping

    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    accessed_keys: list[str] = []

    class LazyMapping(Mapping):
        """Track which keys are accessed."""

        def __init__(self, data: dict) -> None:
            self._data = data

        def __getitem__(self, key: str) -> Any:
            accessed_keys.append(key)
            return self._data[key]

        def __iter__(self):  # noqa: ANN204
            return iter(self._data)

        def __len__(self) -> int:
            return len(self._data)

    mapping = LazyMapping({"x": 10, "y": 20, "unused": 999})
    result = eval_expr_with_mapping("x + y", mapping)
    assert result == 30
    assert "x" in accessed_keys
    assert "y" in accessed_keys
    assert "unused" not in accessed_keys


def test_eval_expr_with_mapping_null_propagation() -> None:
    """Null propagation works through the Mapping path."""
    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    assert eval_expr_with_mapping("{x} + {y}", {"x": None, "y": 2}) is None


def test_eval_expr_with_mapping_none_literal() -> None:
    """The literal 'None' returns None through the Mapping path."""
    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    assert eval_expr_with_mapping("None", {}) is None


# ---- Strict mode for unbound names (issue #213) ----


def test_eval_unbound_name_default_returns_none() -> None:
    """Non-strict (default) returns None for unbound names, preserving SQL-null semantics."""
    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    assert eval_expr_with_mapping("{scroe}", {"score": 5}) is None  # codespell:ignore


def test_eval_unbound_name_default_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Non-strict emits a warning so the unbound reference is not entirely silent."""
    import logging

    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    with caplog.at_level(logging.WARNING, logger="linkml_map.utils.eval_utils"):
        result = eval_expr_with_mapping("{scroe}", {"score": 5})  # codespell:ignore

    assert result is None
    assert any("scroe" in rec.message for rec in caplog.records)  # codespell:ignore


def test_eval_unbound_name_strict_raises() -> None:
    """Strict surfaces unbound names as NameError with the offending name.

    The transformer wraps this as ``TransformationError`` with derivation
    context via ``_slot_error_context``; at the bare-evaluator level it
    is the built-in ``NameError``.
    """
    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    with pytest.raises(NameError, match="scroe"):  # codespell:ignore
        eval_expr_with_mapping("{scroe}", {"score": 5}, strict=True)  # codespell:ignore


def test_eval_bound_name_with_none_value_returns_none_in_strict() -> None:
    """A name that is bound to None resolves to None even in strict mode (real SQL null)."""
    from linkml_map.utils.eval_utils import eval_expr_with_mapping

    assert eval_expr_with_mapping("{score}", {"score": None}, strict=True) is None


# ---- Distribution edge cases ----


def test_distribution_over_empty_list() -> None:
    """Attribute access on an empty list returns an empty list."""
    c = Container(persons=[])
    assert eval_expr("c.persons.name", c=c) == []


def test_distribution_over_single_element_list() -> None:
    """Attribute access on a single-element list returns a single-element list."""
    c = Container(persons=[Person(name="Alice")])
    assert eval_expr("c.persons.name", c=c) == ["Alice"]


# ---- Function distribution edge cases ----


def test_list_functions_do_not_distribute() -> None:
    """List functions (max, min, len) operate on the list as a whole."""
    assert eval_expr("max(items)", items=[1, 5, 2]) == 5
    assert eval_expr("min(items)", items=[3, 1, 2]) == 1
    assert eval_expr("len(items)", items=["a", "b", "c"]) == 3


def test_scalar_functions_distribute_over_lists() -> None:
    """Scalar functions (str, int, abs) distribute over list arguments."""
    assert eval_expr("str(items)", items=[1, 2, 3]) == ["1", "2", "3"]
    assert eval_expr("abs(items)", items=[-1, 2, -3]) == [1, 2, 3]
    assert eval_expr("int(items)", items=["1", "2", "3"]) == [1, 2, 3]


def test_strlen_distributes_on_distributed_attribute() -> None:
    """Verify strlen distributes over results of distributed attribute access."""
    p1 = Person(name="Al")
    p2 = Person(name="Bob")
    c = Container(persons=[p1, p2])
    assert eval_expr("strlen(c.persons.name)", c=c) == [2, 3]


# ---- uuid5 function ----


def test_uuid5_returns_valid_uuid5_string() -> None:
    """Verify _uuid5 returns a valid UUID5 string."""
    result = _uuid5("https://example.org/X", "foo")
    assert UUID_RE.match(result)


def test_uuid5_deterministic() -> None:
    """Verify same inputs produce identical UUIDs."""
    a = _uuid5("https://example.org/X", "foo")
    b = _uuid5("https://example.org/X", "foo")
    assert a == b


def test_uuid5_different_name_gives_different_uuid() -> None:
    """Verify different names produce different UUIDs."""
    a = _uuid5("https://example.org/X", "foo")
    b = _uuid5("https://example.org/X", "bar")
    assert a != b


def test_uuid5_different_namespace_gives_different_uuid() -> None:
    """Verify different namespaces produce different UUIDs."""
    a = _uuid5("https://example.org/A", "foo")
    b = _uuid5("https://example.org/B", "foo")
    assert a != b


def test_uuid5_via_eval_expr() -> None:
    """Verify uuid5 works through eval_expr with literal args."""
    result = eval_expr('uuid5("https://example.org/X", "foo")')
    assert UUID_RE.match(result)


def test_uuid5_eval_expr_with_variable() -> None:
    """Verify uuid5 works with a variable binding."""
    result = eval_expr('uuid5("https://example.org/X", {name})', name="alice")
    assert UUID_RE.match(result)


def test_uuid5_eval_expr_with_concatenation() -> None:
    """Verify uuid5 works with string concatenation in the name arg."""
    result = eval_expr('uuid5("https://example.org/X", "pre_" + {name})', name="alice")
    assert UUID_RE.match(result)
    assert result == _uuid5("https://example.org/X", "pre_alice")


# ---- Numeric-string coercion integration ----


def test_case_with_numeric_string_coercion() -> None:
    """case() works when numeric variables are compared to string literals (#133)."""
    expr = "case(({status} == '1', 'active'), (True, 'inactive'))"
    assert eval_expr(expr, status=1) == "active"
    assert eval_expr(expr, status=0) == "inactive"


def test_ordering_comparison_with_numeric_string_coercion() -> None:
    """Ordering comparisons coerce numeric strings (#133)."""
    assert eval_expr("{x} < '2'", x=1) is True


def test_bool_not_coerced_as_numeric() -> None:
    """Booleans should not be coerced via numeric-string path (#135)."""
    assert eval_expr("{flag} == '0'", flag=True) is False
    assert eval_expr("{flag} == '1'", flag=False) is False


# ---- New list functions ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ("sum([1, 2, 3])", {}, 6),
        ("sum(items)", {"items": [10, 20, 30]}, 60),
        ("sorted([3, 1, 2])", {}, [1, 2, 3]),
        ("sorted(items)", {"items": ["c", "a", "b"]}, ["a", "b", "c"]),
        ("any([False, True, False])", {}, True),
        ("any([False, False])", {}, False),
        ("all([True, True])", {}, True),
        ("all([True, False])", {}, False),
        ("reversed([1, 2, 3])", {}, [3, 2, 1]),
        ("reversed(items)", {"items": ["a", "b", "c"]}, ["c", "b", "a"]),
    ],
    ids=[
        "sum_literal",
        "sum_var",
        "sorted_literal",
        "sorted_var",
        "any_true",
        "any_false",
        "all_true",
        "all_false",
        "reversed_literal",
        "reversed_var",
    ],
)
def test_list_functions_new(expr: str, kwargs: dict, expected: Any) -> None:
    """Test new list aggregate functions."""
    assert eval_expr(expr, **kwargs) == expected


def test_new_list_functions_null_safe() -> None:
    """New list functions return None when given None."""
    assert eval_expr("sum(x)", x=None) is None
    assert eval_expr("sorted(x)", x=None) is None
    assert eval_expr("any(x)", x=None) is None
    assert eval_expr("all(x)", x=None) is None
    assert eval_expr("reversed(x)", x=None) is None


def test_new_list_functions_do_not_distribute() -> None:
    """New list functions operate on the list as a whole, not element-wise."""
    assert eval_expr("sum(items)", items=[1, 2, 3]) == 6
    assert eval_expr("sorted(items)", items=[3, 1, 2]) == [1, 2, 3]


# ---- String functions ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        # Case/formatting
        ('upper("hello")', {}, "HELLO"),
        ('lower("HELLO")', {}, "hello"),
        ('title("hello world")', {}, "Hello World"),
        ('capitalize("hello world")', {}, "Hello world"),
        # Whitespace trimming
        ('strip("  hello  ")', {}, "hello"),
        ('lstrip("  hello  ")', {}, "hello  "),
        ('rstrip("  hello  ")', {}, "  hello"),
        # String content
        ('replace("hello", "l", "r")', {}, "herro"),
        ('startswith("hello", "hell")', {}, True),
        ('startswith("hello", "world")', {}, False),
        ('endswith("hello", "llo")', {}, True),
        ('endswith("hello", "xyz")', {}, False),
        # Splitting/joining
        ('split("a,b,c", ",")', {}, ["a", "b", "c"]),
        ('join(",", ["a", "b", "c"])', {}, "a,b,c"),
    ],
    ids=[
        "upper",
        "lower",
        "title",
        "capitalize",
        "strip",
        "lstrip",
        "rstrip",
        "replace",
        "startswith_true",
        "startswith_false",
        "endswith_true",
        "endswith_false",
        "split",
        "join",
    ],
)
def test_string_functions(expr: str, kwargs: dict, expected: Any) -> None:
    """Test string manipulation functions."""
    assert eval_expr(expr, **kwargs) == expected


def test_string_functions_with_variables() -> None:
    """String functions work with variable bindings."""
    assert eval_expr("upper(name)", name="alice") == "ALICE"
    assert eval_expr("lower(name)", name="BOB") == "bob"
    assert eval_expr("strip(name)", name="  alice  ") == "alice"
    assert eval_expr('replace(name, " ", "_")', name="hello world") == "hello_world"


def test_string_functions_distribute_over_lists() -> None:
    """String functions distribute over list arguments."""
    assert eval_expr("upper(names)", names=["alice", "bob"]) == ["ALICE", "BOB"]
    assert eval_expr("lower(names)", names=["ALICE", "BOB"]) == ["alice", "bob"]
    assert eval_expr("strip(names)", names=["  a  ", "  b  "]) == ["a", "b"]
    assert eval_expr("title(names)", names=["hello world", "foo bar"]) == [
        "Hello World",
        "Foo Bar",
    ]
    assert eval_expr('replace(names, " ", "_")', names=["hello world", "foo bar"]) == [
        "hello_world",
        "foo_bar",
    ]


def test_string_functions_null_propagation() -> None:
    """String functions propagate None."""
    assert eval_expr("upper(x)", x=None) is None
    assert eval_expr("lower(x)", x=None) is None
    assert eval_expr("strip(x)", x=None) is None
    assert eval_expr("replace(x, 'a', 'b')", x=None) is None


def test_string_functions_null_in_list() -> None:
    """String functions handle None elements within lists."""
    assert eval_expr("upper(names)", names=["alice", None, "bob"]) == ["ALICE", None, "BOB"]


def test_split_and_join_roundtrip() -> None:
    """split and join are inverses."""
    assert eval_expr('join(",", split(x, ","))', x="a,b,c") == "a,b,c"


# ---- Type-testing predicates ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ('is_str("hello")', {}, True),
        ("is_str(42)", {}, False),
        ("is_str(x)", {"x": None}, False),
        ("is_int(42)", {}, True),
        ("is_int(3.14)", {}, False),
        ('is_int("42")', {}, False),
        ("is_int(True)", {}, False),
        ("is_float(3.14)", {}, True),
        ("is_float(42)", {}, False),
        ("is_bool(True)", {}, True),
        ("is_bool(False)", {}, True),
        ("is_bool(1)", {}, False),
        ("is_list([1, 2])", {}, True),
        ('is_list("hello")', {}, False),
        ("is_list(x)", {"x": None}, False),
    ],
    ids=[
        "is_str_true",
        "is_str_false",
        "is_str_none",
        "is_int_true",
        "is_int_float",
        "is_int_str",
        "is_int_bool",
        "is_float_true",
        "is_float_false",
        "is_bool_true",
        "is_bool_false",
        "is_bool_int",
        "is_list_true",
        "is_list_false",
        "is_list_none",
    ],
)
def test_type_predicates(expr: str, kwargs: dict, expected: bool) -> None:  # noqa: FBT001
    """Test type-testing predicate functions."""
    assert eval_expr(expr, **kwargs) is expected


def test_type_predicates_in_case() -> None:
    """Type predicates work as guards in case() expressions.

    Note: case() eagerly evaluates all branch values, so the value
    expression must be safe for all inputs. Use str() which handles
    any type, or use if/else for lazy evaluation.
    """
    expr = 'case((is_str(x), upper(x)), (True, "other"))'
    assert eval_expr(expr, x="hello") == "HELLO"
    # if/else is lazy — only the taken branch is evaluated
    assert eval_expr("upper(x) if is_str(x) else str(x)", x="hello") == "HELLO"
    assert eval_expr("upper(x) if is_str(x) else str(x)", x=42) == "42"


# ---- contains ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ('contains("hello world", "world")', {}, True),
        ('contains("hello world", "xyz")', {}, False),
        ('contains(x, "ell")', {"x": "hello"}, True),
        ('contains(x, "ell")', {"x": "world"}, False),
    ],
    ids=["literal_true", "literal_false", "var_true", "var_false"],
)
def test_contains(expr: str, kwargs: dict, expected: bool) -> None:  # noqa: FBT001
    """Test substring containment."""
    assert eval_expr(expr, **kwargs) is expected


def test_contains_distributes_over_list() -> None:
    """contains distributes over lists, returning per-element booleans."""
    assert eval_expr('contains(names, "li")', names=["alice", "bob", "charlie"]) == [
        True,
        False,
        True,
    ]


def test_contains_null_propagation() -> None:
    """contains returns None for None input."""
    assert eval_expr('contains(x, "a")', x=None) is None


def test_contains_null_in_list() -> None:
    """contains handles None elements in lists."""
    assert eval_expr('contains(names, "a")', names=["alice", None, "bob"]) == [True, None, False]


# ---- coalesce ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ('coalesce(None, "fallback")', {}, "fallback"),
        ('coalesce("hello", "fallback")', {}, "hello"),
        ('coalesce(None, None, "last")', {}, "last"),
        ("coalesce(None, None)", {}, None),
        ('coalesce(x, "default")', {"x": "value"}, "value"),
        ('coalesce(x, "default")', {"x": None}, "default"),
        ("coalesce(x, y)", {"x": None, "y": 42}, 42),
    ],
    ids=[
        "none_then_string",
        "string_then_string",
        "two_nones_then_string",
        "all_none",
        "var_present",
        "var_none",
        "two_vars",
    ],
)
def test_coalesce(expr: str, kwargs: dict, expected: Any) -> None:
    """Test coalesce returns first non-None argument."""
    assert eval_expr(expr, **kwargs) == expected


def test_coalesce_preserves_falsy_values() -> None:
    """coalesce treats 0, '', False, [] as present (not None)."""
    assert eval_expr("coalesce(x, 99)", x=0) == 0
    assert eval_expr('coalesce(x, "default")', x="") == ""
    assert eval_expr("coalesce(x, True)", x=False) is False
    assert eval_expr('coalesce(x, "default")', x=[]) == []


def test_coalesce_with_expression_chains() -> None:
    """coalesce composes with other functions."""
    assert eval_expr('upper(coalesce(x, "unknown"))', x=None) == "UNKNOWN"
    assert eval_expr('upper(coalesce(x, "unknown"))', x="alice") == "ALICE"


# ---- first / last ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ("first([10, 20, 30])", {}, 10),
        ("first(items)", {"items": ["a", "b", "c"]}, "a"),
        ("first(items)", {"items": []}, None),
        ("last([10, 20, 30])", {}, 30),
        ("last(items)", {"items": ["a", "b", "c"]}, "c"),
        ("last(items)", {"items": []}, None),
    ],
    ids=[
        "first_literal",
        "first_var",
        "first_empty",
        "last_literal",
        "last_var",
        "last_empty",
    ],
)
def test_first_last(expr: str, kwargs: dict, expected: Any) -> None:
    """Test first/last element access."""
    assert eval_expr(expr, **kwargs) == expected


def test_first_last_null_safe() -> None:
    """first/last return None when given None."""
    assert eval_expr("first(x)", x=None) is None
    assert eval_expr("last(x)", x=None) is None


def test_first_last_with_split() -> None:
    """first/last compose naturally with split."""
    assert eval_expr('first(split(x, "="))', x="key=value") == "key"
    assert eval_expr('last(split(x, "="))', x="key=value") == "value"


# ---- floor / ceil ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ("floor(3.7)", {}, 3),
        ("floor(3.2)", {}, 3),
        ("floor(-1.5)", {}, -2),
        ("floor(x)", {"x": 4.9}, 4),
        ("ceil(3.2)", {}, 4),
        ("ceil(3.7)", {}, 4),
        ("ceil(-1.5)", {}, -1),
        ("ceil(x)", {"x": 4.1}, 5),
    ],
    ids=[
        "floor_down",
        "floor_near",
        "floor_negative",
        "floor_var",
        "ceil_up",
        "ceil_near",
        "ceil_negative",
        "ceil_var",
    ],
)
def test_floor_ceil(expr: str, kwargs: dict, expected: int) -> None:
    """Test floor/ceil rounding."""
    assert eval_expr(expr, **kwargs) == expected


def test_floor_ceil_null_propagation() -> None:
    """floor/ceil propagate None via _distributing."""
    assert eval_expr("floor(x)", x=None) is None
    assert eval_expr("ceil(x)", x=None) is None


def test_floor_ceil_distribute_over_list() -> None:
    """floor/ceil distribute over lists."""
    assert eval_expr("floor(vals)", vals=[1.1, 2.9, 3.5]) == [1, 2, 3]
    assert eval_expr("ceil(vals)", vals=[1.1, 2.9, 3.5]) == [2, 3, 4]


# ---- substr ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ('substr("abcdef", 0, 3)', {}, "abc"),
        ('substr("abcdef", 2)', {}, "cdef"),
        ('substr("20240101", 0, 4)', {}, "2024"),
        ('substr("20240101", 4, 6)', {}, "01"),
        ("substr(x, 0, 4)", {"x": "20240101"}, "2024"),
    ],
    ids=[
        "start_end",
        "start_only",
        "year_extract",
        "mid_extract",
        "with_var",
    ],
)
def test_substr(expr: str, kwargs: dict, expected: str) -> None:
    """Test substring extraction."""
    assert eval_expr(expr, **kwargs) == expected


def test_substr_null_propagation() -> None:
    """substr propagates None."""
    assert eval_expr("substr(x, 0, 3)", x=None) is None


def test_substr_distributes_over_list() -> None:
    """substr distributes over lists."""
    assert eval_expr("substr(dates, 0, 4)", dates=["20240101", "20230615"]) == [
        "2024",
        "2023",
    ]


def test_substr_null_in_list() -> None:
    """substr handles None elements in lists."""
    assert eval_expr("substr(dates, 0, 4)", dates=["20240101", None, "20230615"]) == [
        "2024",
        None,
        "2023",
    ]


# ---- slugify ----


@pytest.mark.parametrize(
    ("expr", "kwargs", "expected"),
    [
        ('slugify("Hello, World!")', {}, "hello_world"),
        ('slugify("Schöne Grüße")', {}, "schone_grusse"),
        ('slugify("Smith, J.R. (Jr.)")', {}, "smith_j_r_jr"),
        ('slugify("123 hits")', {}, "_123_hits"),
        ('slugify("9lives", "-")', {}, "-9lives"),
        ('slugify("café-au-lait", "-")', {}, "cafe-au-lait"),
        ("slugify(x)", {"x": "Hello World"}, "hello_world"),
    ],
    ids=["basic", "unicode", "punctuation", "leading_digit", "leading_digit_dash_sep", "dash_sep", "with_var"],
)
def test_slugify(expr: str, kwargs: dict, expected: str) -> None:
    """slugify converts arbitrary strings to identifier-shaped slugs."""
    assert eval_expr(expr, **kwargs) == expected


@pytest.mark.parametrize(
    "expr",
    ['slugify("")', 'slugify("!!!")', 'slugify("   ")'],
    ids=["empty", "all_punct", "all_whitespace"],
)
def test_slugify_no_content_returns_none(expr: str) -> None:
    """slugify returns None when no identifier-shaped content remains."""
    assert eval_expr(expr) is None


def test_slugify_null_propagation() -> None:
    """slugify propagates None."""
    assert eval_expr("slugify(x)", x=None) is None


def test_slugify_distributes_over_list() -> None:
    """slugify distributes over lists."""
    assert eval_expr("slugify(names)", names=["Foo Bar", "Baz Qux"]) == ["foo_bar", "baz_qux"]


def test_slugify_composes_with_or_fallback() -> None:
    """slugify returning None composes with ``or`` for fallback chains."""
    assert eval_expr('slugify(x) or "anonymous"', x="!!!") == "anonymous"


# ---- to_snake / to_camel / to_pascal ----


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ('to_snake("CamelCase")', "camel_case"),
        ('to_snake("HTTPResponse")', "http_response"),
        ('to_pascal("snake_case")', "SnakeCase"),
        ('to_pascal("http_response")', "HttpResponse"),
        ('to_camel("snake_case")', "snakeCase"),
        ('to_camel("http_response")', "httpResponse"),
    ],
    ids=[
        "snake_from_camel",
        "snake_from_acronym",
        "pascal_from_snake",
        "pascal_two_word",
        "camel_from_snake",
        "camel_two_word",
    ],
)
def test_case_converters(expr: str, expected: str) -> None:
    """Case converters wrap inflection.underscore / inflection.camelize."""
    assert eval_expr(expr) == expected


def test_case_converters_distribute_and_propagate_none() -> None:
    """Case converters share the standard distributing + null-propagating wrapper."""
    assert eval_expr("to_snake(x)", x=None) is None
    assert eval_expr("to_pascal(x)", x=["snake_case", "http_response"]) == [
        "SnakeCase",
        "HttpResponse",
    ]


def test_qualified_unknown_root_fails_loud() -> None:
    """A qualified ``{Unknown.col}`` whose root is unbound raises, even non-strict.

    Distinct from a bare ``{missing}`` (legitimate SQL null) and a known-but-None
    root (sparse-join miss), both of which stay null.
    """
    with pytest.raises(NameError, match="unknown 'Nope'"):
        eval_expr("{Nope.col}", a=1)


def test_bare_absent_and_known_none_stay_null() -> None:
    """Bare absent names and known-but-None roots null out rather than raising."""
    assert eval_expr("{missing}", a=1) is None
    assert eval_expr("{a.b}", a=None) is None


# -- caching / evaluator-reuse regression tests (issue #277) --


@pytest.fixture
def _reset_eval_caches() -> None:
    """Clear the parse cache and per-thread evaluator pool for isolated observation."""
    _parse_cached.cache_clear()
    if hasattr(_evaluator_pool, "by_strict"):
        _evaluator_pool.by_strict.clear()


def test_repeated_expr_parsed_once(_reset_eval_caches: None) -> None:
    """A repeated expression is parsed once, not once per row (issue #277)."""
    rows = 50
    for i in range(rows):
        eval_expr_with_mapping("a + b", {"a": i, "b": 1})
    info = _parse_cached.cache_info()
    assert info.misses == 1
    assert info.hits == rows - 1


def test_evaluator_reused_across_rows(_reset_eval_caches: None) -> None:
    """The evaluator is built once and reused, not reconstructed per row (issue #277)."""
    eval_expr_with_mapping("a + b", {"a": 1, "b": 2})
    first = _evaluator_pool.by_strict[False]
    for i in range(50):
        eval_expr_with_mapping("a + b", {"a": i, "b": 2})
    assert _evaluator_pool.by_strict[False] is first


def test_reused_evaluator_swaps_bindings_per_row(_reset_eval_caches: None) -> None:
    """Reusing the evaluator still binds each row's values independently."""
    results = [eval_expr_with_mapping("a * 2", {"a": i}) for i in range(5)]
    assert results == [0, 2, 4, 6, 8]


def test_strict_and_nonstrict_use_separate_evaluators(_reset_eval_caches: None) -> None:
    """strict and non-strict share the pool key by ``strict`` and don't collide."""
    eval_expr_with_mapping("a + 1", {"a": 1}, strict=False)
    eval_expr_with_mapping("a + 1", {"a": 1}, strict=True)
    assert _evaluator_pool.by_strict[False] is not _evaluator_pool.by_strict[True]
    assert _evaluator_pool.by_strict[False].strict is False
    assert _evaluator_pool.by_strict[True].strict is True


def test_reused_evaluator_applies_per_call_functions(_reset_eval_caches: None) -> None:
    """Per-call functions (e.g. a row-specific ``slot`` closure) are applied on reuse."""
    assert eval_expr_with_mapping("f(2)", {}, functions={"f": lambda x: x + 10}) == 12
    # A subsequent call with a different closure must see the new function, not a stale one.
    assert eval_expr_with_mapping("f(2)", {}, functions={"f": lambda x: x * 10}) == 20
