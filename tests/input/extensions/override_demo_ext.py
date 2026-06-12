"""Test fixture: ``slugify`` extension with distinct output to verify that
``override=True`` actually shadows the built-in through the full transformer
stack, not just at the loader layer.
"""

from linkml_map.utils.extensions import safe_function


@safe_function(override=True)
def slugify(s: str, separator: str = "_") -> str:
    """Deliberately distinct slugify so test assertions can prove the override fired."""
    return f"EXT:{s}"
