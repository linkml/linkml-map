"""Tests for eval_utils, focusing on the uuid5 function."""

import re

from linkml_map.utils.eval_utils import _uuid5, eval_expr

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


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
