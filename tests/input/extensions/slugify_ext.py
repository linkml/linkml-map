"""Example extension module: a minimal pure-stdlib ``slugify``.

Dogfood reference for the ``@safe_function`` extension mechanism. The built-in
``slugify`` (backed by ``python-slugify``) is the production version; this
example exists to demonstrate both how to write an extension and how
``override=True`` shadows a built-in.
"""

import re
import unicodedata

from linkml_map.utils.extensions import safe_function


@safe_function(override=True)
def slugify(s: str, separator: str = "_") -> str | None:
    """ASCII-fold, lowercase, collapse non-alphanumeric runs to ``separator``.

    Returns ``None`` if no identifier-shaped content remains, matching the
    SQL-style null convention so it composes with ``or``-chains in expressions::

        expr: "slugify(name) or 'anonymous'"
    """
    folded = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()
    cleaned = re.sub(r"[^a-z0-9]+", separator, folded).strip(separator)
    if not cleaned:
        return None
    if cleaned[0].isdigit():
        cleaned = separator + cleaned
    return cleaned
