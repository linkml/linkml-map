"""The top-level package's public API."""

import linkml_map


def test_all_names_resolve():
    """Every name in ``__all__`` exists, so ``from linkml_map import *`` works."""
    assert [name for name in linkml_map.__all__ if not hasattr(linkml_map, name)] == []
