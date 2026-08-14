"""Tests for the standalone spec normalizer and its scan phase."""

import subprocess
import sys
import warnings

import pytest

from linkml_map.spec_normalizer import normalize_spec
from linkml_map.transformer.errors import SpecificationError


def test_normalizer_does_not_import_the_validator() -> None:
    """The normalizer must not drag the validator in — that was the import cycle.

    Run in a fresh interpreter so an already-imported validator from another
    test module can't mask a regression.
    """
    code = "import sys, linkml_map.spec_normalizer; print('linkml_map.validator' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "False"


def test_normalize_spec_expands_compact_keys_and_injects_names() -> None:
    """Compact-key list entries become explicit-name dicts (the SHAPE phase)."""
    spec = {
        "id": "https://example.org/test",
        "name": "test",
        "class_derivations": [{"Person": {"populated_from": "Individual"}}],
    }
    normalize_spec(spec)
    (cd,) = spec["class_derivations"]
    assert cd["name"] == "Person"
    assert cd["populated_from"] == "Individual"


def test_normalize_spec_migrates_pv_sources_and_reports_it() -> None:
    """MIGRATE clears PV ``sources`` into ``populated_from``; SCAN reports the deprecation."""
    spec = {
        "id": "https://example.org/test",
        "name": "test",
        "enum_derivations": {
            "ColorEnum": {
                "permissible_value_derivations": {"red": {"sources": "RED"}},
            }
        },
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        messages = normalize_spec(spec)

    pvd = spec["enum_derivations"]["ColorEnum"]["permissible_value_derivations"]["red"]
    assert "sources" not in pvd
    assert pvd["populated_from"] == ["RED"]
    assert any(m.category == "deprecated" for m in messages)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_normalize_spec_silent_returns_errors_instead_of_raising() -> None:
    """``silent=True`` is the validator's path: findings come back as messages."""
    spec = {
        "id": "https://example.org/test",
        "name": "test",
        "enum_derivations": {
            "ColorEnum": {
                "permissible_value_derivations": {"red": {"sources": "RED", "populated_from": ["CRIMSON"]}},
            }
        },
    }
    messages = normalize_spec(spec, silent=True)
    assert [m for m in messages if m.severity == "error"]


def test_normalize_spec_raises_on_conflicting_fields() -> None:
    """Without ``silent``, a scan error aborts the load."""
    spec = {
        "id": "https://example.org/test",
        "name": "test",
        "enum_derivations": {
            "ColorEnum": {
                "permissible_value_derivations": {"red": {"sources": "RED", "populated_from": ["CRIMSON"]}},
            }
        },
    }
    with pytest.raises(SpecificationError, match="populated_from"):
        normalize_spec(spec)
