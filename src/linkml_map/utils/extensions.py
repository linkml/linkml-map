"""Extension surface for downstream-supplied safe functions.

Trans-spec authors register custom functions into the eval namespace by writing
a Python module and tagging functions with :func:`safe_function`. linkml-map
loads these via the ``-F``/``--functions`` CLI flag (repeatable) or the
``extension_functions`` kwarg on :class:`~linkml_map.transformer.object_transformer.ObjectTransformer`.

The decorator is a **declaration by the author** that the function is pure,
bounded-time, and free of I/O. linkml-map does not verify this — the safety
boundary is the named namespace, not sandboxed execution. Same posture as
:func:`typing.final`.

Example
-------
A user-supplied ``my_helpers.py``::

    from linkml_map.utils.extensions import safe_function

    @safe_function
    def slugify(s, separator="_"):
        ...

    @safe_function(override=True)  # explicit shadowing of a built-in
    def lower(s):
        ...

    @safe_function(distributes=False)  # list-style; opts out of scalar distribution
    def my_aggregator(items):
        ...

Then::

    linkml-map map-data ... --functions ./my_helpers.py

Semantics
---------
- Collision between two extensions → :class:`ExtensionError`.
- Collision with a built-in without ``override=True`` → :class:`ExtensionError`.
- ``override=True`` declared but no matching built-in → ``logging.warning``.
- Missing extension file → :class:`ExtensionError`.

For the contract authors are declaring, see ``docs/expressions/extensions.md``.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from linkml_map.utils.eval_utils import FUNCTIONS, _distributing

_SAFE_FUNCTION_ATTR = "_linkml_safe_function"

logger = logging.getLogger(__name__)


class ExtensionError(Exception):
    """Raised when loading an extension function module fails."""


def safe_function(
    func: Callable | None = None,
    *,
    override: bool = False,
    distributes: bool = True,
) -> Callable:
    """Tag a function for inclusion in the safe-function namespace.

    Applying this decorator is a **declaration by the author** that the
    function is pure, bounded-time, and free of I/O. linkml-map does not
    verify these properties.

    Usable bare or with kwargs::

        @safe_function
        def slugify(s): ...

        @safe_function(override=True)
        def lower(s): ...

    :param override: Allow shadowing a built-in of the same name. Without this,
        a collision with a built-in raises :class:`ExtensionError` at load time.
    :param distributes: Apply the scalar-distributing wrapper (broadcasts over
        lists, propagates ``None``). Default ``True``; set ``False`` for
        functions that accept a list as their first argument.
    """

    def _tag(fn: Callable) -> Callable:
        fn._linkml_safe_function = {"override": override, "distributes": distributes}  # type: ignore[attr-defined]
        return fn

    if func is not None:
        # Bare ``@safe_function`` with no parentheses.
        return _tag(func)
    return _tag


def _load_module_from_path(path: Path) -> Any:  # noqa: ANN401
    """Import a Python file as an anonymous module.

    :raises ExtensionError: If the file does not exist.
    """
    if not path.exists():
        msg = f"Extension file not found: {path}"
        raise ExtensionError(msg)
    spec = importlib.util.spec_from_file_location(f"_linkml_ext_{path.stem}", path)
    if spec is None or spec.loader is None:
        msg = f"Could not create import spec for: {path}"
        raise ExtensionError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _collect_tagged_functions(module: Any) -> dict[str, dict[str, Any]]:  # noqa: ANN401
    """Walk module attributes and collect functions tagged with :func:`safe_function`."""
    found: dict[str, dict[str, Any]] = {}
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        meta = getattr(obj, _SAFE_FUNCTION_ATTR, None)
        if isinstance(meta, dict):
            found[name] = {"func": obj, **meta}
    return found


def load_extensions(paths: Iterable[str | Path]) -> dict[str, Callable]:
    """Load tagged functions from a list of file paths into one merged dict.

    Applies the scalar-distributing wrapper to functions declared with
    ``distributes=True`` (the default), so they broadcast over lists and
    propagate ``None`` consistently with the built-ins.

    :param paths: Iterable of file paths to ``.py`` modules with tagged functions.
    :returns: Mapping of ``name → callable`` ready to merge into
        ``ObjectTransformer.extension_functions``.
    :raises ExtensionError: On missing file, name collision between extensions,
        or attempt to shadow a built-in without ``override=True``.
    """
    merged: dict[str, Callable] = {}
    sources: dict[str, Path] = {}

    for raw_path in paths:
        path = Path(raw_path).resolve()
        module = _load_module_from_path(path)
        tagged = _collect_tagged_functions(module)

        for name, meta in tagged.items():
            if name in merged:
                msg = f"Extension name collision: {name!r} defined in both {sources[name]} and {path}"
                raise ExtensionError(msg)
            if name in FUNCTIONS and not meta["override"]:
                msg = (
                    f"Extension {name!r} from {path} shadows a built-in of the "
                    f"same name. Declare ``@safe_function(override=True)`` if intentional."
                )
                raise ExtensionError(msg)
            if meta["override"] and name not in FUNCTIONS:
                logger.warning(
                    "Extension %r from %s declared override=True but no built-in %r exists",
                    name,
                    path,
                    name,
                )

            fn = meta["func"]
            if meta["distributes"]:
                fn = _distributing(fn)
            merged[name] = fn
            sources[name] = path

    return merged
