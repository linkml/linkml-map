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

For the contract authors are declaring, see ``docs/api/extensions.md``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import logging
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from types import ModuleType
from typing import Any

from linkml_map.utils.eval_utils import FUNCTIONS, _distributing

_SAFE_FUNCTION_ATTR = "_linkml_safe_function"

#: Names injected per-call by the transformer (e.g. ``slot``). Extensions cannot
#: use these — they would be silently shadowed at expression-evaluation time.
_RESERVED_NAMES: frozenset[str] = frozenset({"slot"})

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
        setattr(fn, _SAFE_FUNCTION_ATTR, {"override": override, "distributes": distributes})
        return fn

    if func is not None:
        # Bare ``@safe_function`` with no parentheses.
        return _tag(func)
    return _tag


def _load_module_from_path(path: Path) -> ModuleType:
    """Import a Python file as an anonymous module.

    The ``sys.modules`` registration key includes a short hash of the resolved
    path so two extension files sharing a basename (e.g. ``a/helpers.py`` and
    ``b/helpers.py``) don't clobber each other. On import-time failure, the
    half-initialized entry is removed and the underlying exception is wrapped
    as :class:`ExtensionError` with path context.

    :raises ExtensionError: If the file does not exist, the spec cannot be
        constructed, or the module raises during import.
    """
    if not path.exists():
        msg = f"Extension file not found: {path}"
        raise ExtensionError(msg)
    path_hash = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:8]  # noqa: S324
    spec_name = f"_linkml_ext_{path.stem}_{path_hash}"
    spec = importlib.util.spec_from_file_location(spec_name, path)
    if spec is None or spec.loader is None:
        msg = f"Could not create import spec for: {path}"
        raise ExtensionError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(spec_name, None)
        msg = f"Failed to import extension {path}: {type(exc).__name__}: {exc}"
        raise ExtensionError(msg) from exc
    return module


def _collect_tagged_functions(module: ModuleType) -> dict[str, dict[str, Any]]:
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
            if name in _RESERVED_NAMES:
                msg = (
                    f"Extension name {name!r} from {path} is reserved — the "
                    f"transformer injects it per-call, so it would silently "
                    f"shadow your extension. Pick a different name."
                )
                raise ExtensionError(msg)
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
