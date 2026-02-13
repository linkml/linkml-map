"""Tests for eval_utils, focusing on the uuid5 function."""

import re

from linkml_map.utils.eval_utils import _uuid5, eval_expr

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


class TestUuid5:
    """Tests for the _uuid5 helper."""

    def test_returns_valid_uuid5_string(self) -> None:
        """Verify _uuid5 returns a valid UUID5 string."""
        result = _uuid5("https://example.org/X", "foo")
        assert UUID_RE.match(result)

    def test_deterministic(self) -> None:
        """Verify same inputs produce identical UUIDs."""
        a = _uuid5("https://example.org/X", "foo")
        b = _uuid5("https://example.org/X", "foo")
        assert a == b

    def test_different_name_gives_different_uuid(self) -> None:
        """Verify different names produce different UUIDs."""
        a = _uuid5("https://example.org/X", "foo")
        b = _uuid5("https://example.org/X", "bar")
        assert a != b

    def test_different_namespace_gives_different_uuid(self) -> None:
        """Verify different namespaces produce different UUIDs."""
        a = _uuid5("https://example.org/A", "foo")
        b = _uuid5("https://example.org/B", "foo")
        assert a != b


class TestEvalExprUuid5:
    """Tests for uuid5 through the safe eval path."""

    def test_uuid5_via_eval_expr(self) -> None:
        """Verify uuid5 works through eval_expr with literal args."""
        result = eval_expr('uuid5("https://example.org/X", "foo")')
        assert UUID_RE.match(result)

    def test_uuid5_with_variable(self) -> None:
        """Verify uuid5 works with a variable binding."""
        result = eval_expr('uuid5("https://example.org/X", {name})', name="alice")
        assert UUID_RE.match(result)

    def test_uuid5_with_concatenation(self) -> None:
        """Verify uuid5 works with string concatenation in the name arg."""
        result = eval_expr('uuid5("https://example.org/X", "pre_" + {name})', name="alice")
        assert UUID_RE.match(result)
        assert result == _uuid5("https://example.org/X", "pre_alice")
