"""Tests for the safe-function extension mechanism."""

# ruff: noqa: ANN401, PLR2004

import logging
import sys
from pathlib import Path

import pytest

from linkml_map.utils.eval_utils import (
    FUNCTIONS,
    UnknownFunctionError,
    eval_expr,
    eval_expr_with_mapping,
    suggest_for_unknown_name,
)
from linkml_map.utils.extensions import (
    _SAFE_FUNCTION_ATTR,
    ExtensionError,
    load_extensions,
    safe_function,
)


def _write_ext(tmp_path: Path, name: str, body: str) -> Path:
    """Write an extension module file and return its path."""
    path = tmp_path / name
    path.write_text(body)
    return path


# ---- Decorator ----


def test_decorator_bare() -> None:
    """``@safe_function`` without parentheses tags the function."""

    @safe_function
    def f(x: str) -> str:
        return x.upper()

    meta = getattr(f, _SAFE_FUNCTION_ATTR)
    assert meta == {"override": False, "distributes": True}
    assert f("hi") == "HI"


def test_decorator_with_kwargs() -> None:
    """``@safe_function(override=True, distributes=False)`` carries kwargs."""

    @safe_function(override=True, distributes=False)
    def f(items: list) -> int:
        return len(items)

    meta = getattr(f, _SAFE_FUNCTION_ATTR)
    assert meta == {"override": True, "distributes": False}


# ---- Loader ----


def test_load_single_extension(tmp_path: Path) -> None:
    """Loading a single file picks up all tagged functions."""
    path = _write_ext(
        tmp_path,
        "ext1.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def reverse(s):
    return s[::-1]

@safe_function
def double(s):
    return s + s

def untagged(s):
    return s  # should be ignored
""",
    )

    loaded = load_extensions([path])

    assert set(loaded.keys()) == {"reverse", "double"}
    assert loaded["reverse"]("abc") == "cba"


def test_load_multiple_extensions(tmp_path: Path) -> None:
    """Loading multiple files merges their tagged functions."""
    a = _write_ext(
        tmp_path,
        "a.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def alpha(s):
    return "A:" + s
""",
    )
    b = _write_ext(
        tmp_path,
        "b.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def beta(s):
    return "B:" + s
""",
    )

    loaded = load_extensions([a, b])

    assert set(loaded.keys()) == {"alpha", "beta"}
    assert loaded["alpha"]("x") == "A:x"
    assert loaded["beta"]("y") == "B:y"


def test_collision_between_extensions(tmp_path: Path) -> None:
    """Two extensions defining the same name → ExtensionError."""
    a = _write_ext(
        tmp_path,
        "a.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def shared(s):
    return "A:" + s
""",
    )
    b = _write_ext(
        tmp_path,
        "b.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def shared(s):
    return "B:" + s
""",
    )

    with pytest.raises(ExtensionError, match="collision"):
        load_extensions([a, b])


def test_collision_with_builtin_without_override(tmp_path: Path) -> None:
    """Shadowing a built-in without override=True → ExtensionError."""
    path = _write_ext(
        tmp_path,
        "ext.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def lower(s):
    return s
""",
    )

    with pytest.raises(ExtensionError, match="shadows a built-in"):
        load_extensions([path])


def test_collision_with_builtin_with_override(tmp_path: Path) -> None:
    """Shadowing a built-in with override=True succeeds and replaces it."""
    path = _write_ext(
        tmp_path,
        "ext.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function(override=True)
def lower(s):
    return "OVERRIDDEN:" + s
""",
    )

    loaded = load_extensions([path])

    assert loaded["lower"]("hi") == "OVERRIDDEN:hi"


def test_override_without_existing_builtin_warns(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """override=True declared but no matching built-in → warning, no error."""
    path = _write_ext(
        tmp_path,
        "ext.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function(override=True)
def no_such_builtin(s):
    return s
""",
    )

    with caplog.at_level(logging.WARNING, logger="linkml_map.utils.extensions"):
        loaded = load_extensions([path])

    assert "no_such_builtin" in loaded
    assert any("override=True" in r.message for r in caplog.records)


def test_missing_file_errors(tmp_path: Path) -> None:
    """A missing extension file → ExtensionError."""
    missing = tmp_path / "nope.py"
    with pytest.raises(ExtensionError, match="not found"):
        load_extensions([missing])


# ---- Wrapper behavior: distribution and None propagation ----


def test_distributing_applied_by_default(tmp_path: Path) -> None:
    """Scalar extensions distribute over lists and propagate None by default."""
    path = _write_ext(
        tmp_path,
        "ext.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def shout(s):
    return s.upper() + "!"
""",
    )

    loaded = load_extensions([path])

    assert loaded["shout"]("hi") == "HI!"
    assert loaded["shout"](["a", "b"]) == ["A!", "B!"]
    assert loaded["shout"](None) is None


def test_distributes_false_keeps_list_intact(tmp_path: Path) -> None:
    """``distributes=False`` does not apply the distributing wrapper."""
    path = _write_ext(
        tmp_path,
        "ext.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function(distributes=False)
def join_them(items):
    return ",".join(items)
""",
    )

    loaded = load_extensions([path])

    # Receives the list as-is, doesn't distribute.
    assert loaded["join_them"](["a", "b", "c"]) == "a,b,c"


# ---- Integration with the evaluator ----


def test_extension_callable_via_eval_expr_with_mapping(tmp_path: Path) -> None:
    """Extension functions plug into the evaluator via the ``functions`` kwarg."""
    path = _write_ext(
        tmp_path,
        "ext.py",
        """
from linkml_map.utils.extensions import safe_function

@safe_function
def excited(s):
    return s + "!"
""",
    )
    loaded = load_extensions([path])

    result = eval_expr_with_mapping("excited(name)", {"name": "hi"}, functions=loaded)

    assert result == "hi!"


# ---- Unknown function errors ----


def test_unknown_function_raises_enriched_error() -> None:
    """An unknown function name raises UnknownFunctionError with a helpful message."""
    with pytest.raises(UnknownFunctionError) as exc_info:
        eval_expr("no_such_helper('hello world')")

    err = exc_info.value
    assert err.func_name == "no_such_helper"
    assert "Unknown function 'no_such_helper'" in str(err)
    assert "--functions" in str(err)


def test_unknown_function_includes_did_you_mean() -> None:
    """Close matches in the known pool show up as did-you-mean suggestions."""
    with pytest.raises(UnknownFunctionError) as exc_info:
        # ``lwer`` is close to ``lower``
        eval_expr("lwer('HELLO')")

    assert "'lower'" in str(exc_info.value)


def test_suggest_for_unknown_name_no_close_match() -> None:
    """Without a close match, no did-you-mean phrase is included."""
    msg = suggest_for_unknown_name("zzqqxx", known_names=FUNCTIONS.keys())
    assert "Did you mean" not in msg
    assert "Unknown function 'zzqqxx'" in msg
    assert "--functions" in msg


# ---- Integration with ObjectTransformer ----

EXTENSIONS_DIR = Path(__file__).parent.parent / "input" / "extensions"


def test_object_transformer_uses_extension_functions() -> None:
    """End-to-end: extension function is callable from a slot derivation expr."""
    from linkml_runtime import SchemaView

    from linkml_map.transformer.object_transformer import ObjectTransformer

    source_schema = """
id: https://example.org/src
name: src
prefixes:
  linkml: https://w3id.org/linkml/
default_prefix: ex
imports: [linkml:types]
classes:
  Person:
    attributes:
      full_name: {range: string}
"""
    target_schema = """
id: https://example.org/tgt
name: tgt
prefixes:
  linkml: https://w3id.org/linkml/
default_prefix: ex
imports: [linkml:types]
classes:
  Agent:
    attributes:
      identifier: {range: string}
"""
    transform_spec = {
        "id": "https://example.org/tr",
        "class_derivations": {
            "Agent": {
                "populated_from": "Person",
                "slot_derivations": {
                    "identifier": {"expr": "slugify(full_name)"},
                },
            }
        },
    }

    extensions = load_extensions([EXTENSIONS_DIR / "slugify_ext.py"])
    tr = ObjectTransformer(extension_functions=extensions)
    tr.source_schemaview = SchemaView(source_schema)
    tr.target_schemaview = SchemaView(target_schema)
    tr.create_transformer_specification(transform_spec)

    result = tr.map_object({"full_name": "Smith, J.R. (Jr.)"}, source_type="Person")

    assert result == {"identifier": "smith_j_r_jr"}


def test_cli_loads_extension_module(tmp_path: Path) -> None:
    """CLI ``--functions`` loads the extension and makes its names available."""
    import yaml
    from click.testing import CliRunner

    from linkml_map.cli.cli import main

    source_schema = tmp_path / "source.yaml"
    source_schema.write_text(
        """
id: https://example.org/src
name: src
prefixes:
  linkml: https://w3id.org/linkml/
default_prefix: ex
imports: [linkml:types]
classes:
  Person:
    attributes:
      full_name: {range: string}
"""
    )
    target_schema = tmp_path / "target.yaml"
    target_schema.write_text(
        """
id: https://example.org/tgt
name: tgt
prefixes:
  linkml: https://w3id.org/linkml/
default_prefix: ex
imports: [linkml:types]
classes:
  Agent:
    attributes:
      identifier: {range: string}
"""
    )
    spec = tmp_path / "spec.yaml"
    spec.write_text(
        """
id: https://example.org/tr
class_derivations:
  Agent:
    populated_from: Person
    slot_derivations:
      identifier:
        expr: "slugify(full_name)"
"""
    )
    data = tmp_path / "person.yaml"
    data.write_text("full_name: 'O''Brien, P.'\n")
    out = tmp_path / "out.yaml"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "map-data",
            "-s",
            str(source_schema),
            "--target-schema",
            str(target_schema),
            "-T",
            str(spec),
            "--functions",
            str(EXTENSIONS_DIR / "slugify_ext.py"),
            "--source-type",
            "Person",
            "-o",
            str(out),
            str(data),
        ],
    )

    assert result.exit_code == 0, result.output
    assert yaml.safe_load(out.read_text()) == {"identifier": "o_brien_p"}


# ---- Loader robustness: import-time errors and module-name collisions ----


def test_import_time_error_raises_extension_error(tmp_path: Path) -> None:
    """SyntaxError in an extension surfaces as ExtensionError, not a traceback."""
    bad = _write_ext(tmp_path, "broken.py", "def f(:\n")
    with pytest.raises(ExtensionError, match="broken.py"):
        load_extensions([bad])
    # sys.modules cleaned up on failure — no half-initialized entry left behind.
    assert not any(k.startswith("_linkml_ext_broken_") for k in sys.modules)


def test_two_files_with_same_basename_do_not_collide(tmp_path: Path) -> None:
    """Two extension files named the same don't clobber each other in sys.modules."""
    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    a_dir.mkdir()
    b_dir.mkdir()
    (a_dir / "helpers.py").write_text(
        "from linkml_map.utils.extensions import safe_function\n@safe_function\ndef alpha(s):\n    return 'A:' + s\n"
    )
    (b_dir / "helpers.py").write_text(
        "from linkml_map.utils.extensions import safe_function\n@safe_function\ndef beta(s):\n    return 'B:' + s\n"
    )

    loaded = load_extensions([a_dir / "helpers.py", b_dir / "helpers.py"])

    # Both functions present — second load didn't clobber the first's module.
    assert loaded["alpha"]("x") == "A:x"
    assert loaded["beta"]("x") == "B:x"


# ---- Reserved-name guard ----


def test_reserved_name_slot_rejected(tmp_path: Path) -> None:
    """Naming an extension 'slot' raises ExtensionError (reserved by the transformer)."""
    path = _write_ext(
        tmp_path,
        "ext.py",
        "from linkml_map.utils.extensions import safe_function\n@safe_function\ndef slot(name):\n    return name\n",
    )
    with pytest.raises(ExtensionError, match="reserved"):
        load_extensions([path])


# ---- Override end-to-end through the transformer ----


def test_override_shadows_builtin_through_transformer() -> None:
    """``override=True`` replaces the built-in inside ObjectTransformer eval,
    not just in the loader dict.

    Uses ``override_demo_ext.py`` which returns ``"EXT:<input>"`` — distinct
    from the built-in ``slugify`` — so the assertion can only pass if the
    extension's function actually fired during evaluation.
    """
    from linkml_runtime import SchemaView

    from linkml_map.transformer.object_transformer import ObjectTransformer

    source_schema = """
id: https://example.org/src
name: src
prefixes:
  linkml: https://w3id.org/linkml/
default_prefix: ex
imports: [linkml:types]
classes:
  Person:
    attributes:
      full_name: {range: string}
"""
    target_schema = """
id: https://example.org/tgt
name: tgt
prefixes:
  linkml: https://w3id.org/linkml/
default_prefix: ex
imports: [linkml:types]
classes:
  Agent:
    attributes:
      identifier: {range: string}
"""
    transform_spec = {
        "id": "https://example.org/tr",
        "class_derivations": {
            "Agent": {
                "populated_from": "Person",
                "slot_derivations": {"identifier": {"expr": "slugify(full_name)"}},
            }
        },
    }

    extensions = load_extensions([EXTENSIONS_DIR / "override_demo_ext.py"])
    tr = ObjectTransformer(extension_functions=extensions)
    tr.source_schemaview = SchemaView(source_schema)
    tr.target_schemaview = SchemaView(target_schema)
    tr.create_transformer_specification(transform_spec)

    result = tr.map_object({"full_name": "Smith"}, source_type="Person")

    assert result == {"identifier": "EXT:Smith"}


# ---- CLI negative path ----


def test_cli_bad_extension_yields_clean_error(tmp_path: Path) -> None:
    """A failing extension load surfaces as a ClickException, not a traceback."""
    from click.testing import CliRunner

    from linkml_map.cli.cli import main

    bad = tmp_path / "broken.py"
    bad.write_text("def f(:\n")  # SyntaxError at import time

    # Other args don't matter — load_extensions fires before file processing.
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["map-data", "-s", "x", "-T", "y", "--functions", str(bad), "in"],
    )

    assert result.exit_code != 0
    assert "broken.py" in result.output
    assert "Traceback" not in result.output
