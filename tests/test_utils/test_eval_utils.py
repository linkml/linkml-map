"""Tests for the restricted expression evaluator."""

# ruff: noqa: ANN401, PLR2004

import re
from dataclasses import dataclass, field
from typing import Any, Optional

import pytest

from linkml_map.utils.eval_utils import UnsetValueError, _uuid5, eval_expr

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
        "add", "sub", "mul", "div", "floordiv", "mod",
        "pow", "xor", "neg", "precedence", "str_concat", "list_concat",
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
        "eq", "ne_true", "ne_false",
        "lt_true", "lt_false", "le_true", "le_false",
        "gt_true", "gt_false", "ge_true", "ge_false",
        "is_none", "is_not_none", "is_not_none_true", "is_not_none_false",
        "in_str_true", "in_str_false", "not_in_true", "not_in_false",
        "in_list_true", "in_list_false",
        "chained_lt_lt", "chained_lt_gt", "chained_le_lt",
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
        "and_tt", "and_tf", "or_ft", "or_ff",
        "not_t", "not_f", "and_not", "not_or",
        "multi_and_t", "multi_and_f", "multi_or_t", "multi_or_f",
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
    """If a {var} is None, the entire expression evaluates to None."""
    assert eval_expr("{x} + {y}", x=None, y=2) is None


def test_null_propagation_both_none() -> None:
    """Null propagation works when all variables are None."""
    assert eval_expr("{x} + {y}", x=None, y=None) is None


def test_bare_none_no_propagation() -> None:
    """Bare variables (no braces) do NOT trigger null propagation."""
    assert eval_expr("'NOT_NULL' if x else 'NULL'", x=None) == "NULL"
    assert eval_expr("'NOT_NULL' if x else 'NULL'", x=1) == "NOT_NULL"


def test_unbound_variable() -> None:
    """An unbound variable resolves to None."""
    assert eval_expr("x") is None


def test_none_expression_literal() -> None:
    """The literal string 'None' evaluates to None."""
    assert eval_expr("None") is None


def test_list_variable_concatenation() -> None:
    """List variables can be concatenated."""
    assert eval_expr("{x} + {y}", x=["a", "b"], y=["c", "d"]) == ["a", "b", "c", "d"]


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
        "max", "max_var", "min", "len", "strlen", "strlen_concat",
        "str", "int", "float", "bool_true", "bool_false", "abs", "round",
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
    """Calling an unknown function raises an error."""
    with pytest.raises(Exception, match="[Nn]ot defined"):  # codespell:ignore
        eval_expr("my_func(1)")


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
    from simpleeval import FunctionNotDefined

    with pytest.raises(FunctionNotDefined):
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


def test_unset_value_error_raised() -> None:
    """UnsetValueError is raised for None-valued {var} references."""
    from linkml_map.utils.eval_utils import LinkMLEvaluator

    evaluator = LinkMLEvaluator(names={"x": None})
    with pytest.raises(UnsetValueError):
        evaluator.eval("{x}")


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
