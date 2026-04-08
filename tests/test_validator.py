"""Tests for transformation specification validation."""

import pytest

from linkml_map.validator import normalize_spec_dict, validate_spec, validate_spec_file
from tests import EXAMPLE_DIR

# ---------------------------------------------------------------------------
# Unit tests for normalize_spec_dict
# ---------------------------------------------------------------------------


def test_normalize_dict_keyed_format():
    """Dict-keyed class_derivations are converted to explicit list."""
    raw = {
        "class_derivations": {
            "Foo": {"populated_from": "Bar"},
            "Baz": None,
        }
    }
    result = normalize_spec_dict(raw)
    cd = result["class_derivations"]
    assert isinstance(cd, list)
    names = [item["name"] for item in cd]
    assert "Foo" in names
    assert "Baz" in names


def test_normalize_compact_key_list_format():
    """Compact-key list format is expanded to have explicit name field."""
    raw = {
        "class_derivations": [
            {"Foo": {"populated_from": "Bar"}},
            {"Baz": None},
        ]
    }
    result = normalize_spec_dict(raw)
    cd = result["class_derivations"]
    assert isinstance(cd, list)
    assert cd[0]["name"] == "Foo"
    assert cd[0]["populated_from"] == "Bar"
    assert cd[1]["name"] == "Baz"


def test_normalize_explicit_list_format():
    """Explicit list format passes through unchanged."""
    raw = {
        "class_derivations": [
            {"name": "Foo", "populated_from": "Bar"},
        ]
    }
    result = normalize_spec_dict(raw)
    cd = result["class_derivations"]
    assert cd[0]["name"] == "Foo"


@pytest.mark.parametrize("version,expected", [(0.1, "0.1"), (1, "1"), (2, "2")])
def test_normalize_coerces_version(version, expected):
    """Numeric version values are coerced to string."""
    raw = {"version": version}
    result = normalize_spec_dict(raw)
    assert result["version"] == expected


def test_normalize_coerces_publication_date():
    """Date objects are coerced to ISO format strings."""
    from datetime import date

    raw = {"publication_date": date(2025, 8, 14)}
    result = normalize_spec_dict(raw)
    assert result["publication_date"] == "2025-08-14"


# ---------------------------------------------------------------------------
# Unit tests for validate_spec
# ---------------------------------------------------------------------------


def test_validate_valid_dict_keyed_spec():
    """A minimal valid spec in dict-keyed format passes validation."""
    spec = {
        "class_derivations": {
            "Agent": {"populated_from": "Person"},
        }
    }
    errors = validate_spec(spec)
    assert errors == []


def test_validate_valid_explicit_list_spec():
    """A minimal valid spec in explicit list format passes validation."""
    spec = {
        "class_derivations": [
            {"name": "Agent", "populated_from": "Person"},
        ]
    }
    errors = validate_spec(spec)
    assert errors == []


def test_validate_valid_compact_key_list_spec():
    """A minimal valid spec in compact-key list format passes validation."""
    spec = {
        "class_derivations": [
            {"Agent": {"populated_from": "Person"}},
        ]
    }
    errors = validate_spec(spec)
    assert errors == []


def test_validate_multiple_derivations_same_class():
    """Multiple derivations for the same class name validate in list format."""
    spec = {
        "class_derivations": [
            {"name": "Measurement", "populated_from": "table_a"},
            {"name": "Measurement", "populated_from": "table_b"},
        ]
    }
    errors = validate_spec(spec)
    assert errors == []


def test_validate_detects_invalid_field():
    """An unknown top-level field is rejected."""
    spec = {
        "class_derivations": {},
        "not_a_real_field": "oops",
    }
    errors = validate_spec(spec)
    assert len(errors) > 0
    assert any("not_a_real_field" in e for e in errors)


def test_validate_detects_bad_slot_derivation_type():
    """A slot_derivation with a non-dict value is rejected."""
    spec = {
        "class_derivations": [
            {
                "name": "Agent",
                "populated_from": "Person",
                "slot_derivations": {"id": "not_a_dict"},
            },
        ]
    }
    errors = validate_spec(spec)
    assert len(errors) > 0


# ---------------------------------------------------------------------------
# File-level validation against real trans-specs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spec_file",
    sorted(EXAMPLE_DIR.rglob("*.transform.yaml")),
    ids=lambda p: str(p.relative_to(EXAMPLE_DIR)),
)
def test_validate_all_example_specs(spec_file):
    """All bundled example trans-specs pass validation."""
    errors = validate_spec_file(spec_file)
    assert errors == [], f"Validation errors in {spec_file.name}:\n" + "\n".join(errors)


def test_validate_non_mapping_file(tmp_path):
    """A YAML file that is a list (not a mapping) reports an error."""
    f = tmp_path / "bad.yaml"
    f.write_text("- item1\n- item2\n")
    errors = validate_spec_file(f)
    assert len(errors) == 1
    assert "mapping" in errors[0].lower()
