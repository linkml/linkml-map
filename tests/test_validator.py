"""Tests for transformation specification validation."""

import pytest

from linkml_map.validator import (
    ValidationMessage,
    extract_expr_slot_references,
    normalize_spec_dict,
    validate_spec,
    validate_spec_file,
    validate_spec_semantics,
)
from tests import (
    EXAMPLE_DIR,
    FLATTENING_SRC_SCHEMA,
    FLATTENING_TGT_SCHEMA,
    FLATTENING_TR,
    PERSONINFO_SRC_SCHEMA,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _errors(messages: list[ValidationMessage]) -> list[ValidationMessage]:
    return [m for m in messages if m.severity == "error"]


def _warnings(messages: list[ValidationMessage]) -> list[ValidationMessage]:
    return [m for m in messages if m.severity == "warning"]


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
# Unit tests for validate_spec (structural)
# ---------------------------------------------------------------------------


def test_validate_valid_dict_keyed_spec():
    """A minimal valid spec in dict-keyed format passes validation."""
    spec = {
        "class_derivations": {
            "Agent": {"populated_from": "Person"},
        }
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []


def test_validate_valid_explicit_list_spec():
    """A minimal valid spec in explicit list format passes validation."""
    spec = {
        "class_derivations": [
            {"name": "Agent", "populated_from": "Person"},
        ]
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []


def test_validate_valid_compact_key_list_spec():
    """A minimal valid spec in compact-key list format passes validation."""
    spec = {
        "class_derivations": [
            {"Agent": {"populated_from": "Person"}},
        ]
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []


def test_validate_multiple_derivations_same_class():
    """Multiple derivations for the same class name validate in list format."""
    spec = {
        "class_derivations": [
            {"name": "Measurement", "populated_from": "table_a"},
            {"name": "Measurement", "populated_from": "table_b"},
        ]
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []


def test_validate_detects_invalid_field():
    """An unknown top-level field is rejected."""
    spec = {
        "class_derivations": {},
        "not_a_real_field": "oops",
    }
    msgs = validate_spec(spec)
    errors = _errors(msgs)
    assert len(errors) > 0
    assert any("not_a_real_field" in m.message for m in errors)


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
    msgs = validate_spec(spec)
    assert len(_errors(msgs)) > 0


# ---------------------------------------------------------------------------
# PermissibleValueDerivation populated_from / sources interaction
# ---------------------------------------------------------------------------


def test_pv_populated_from_list_validates():
    """List-form populated_from on a PV deriv is structurally valid."""
    spec = {
        "enum_derivations": {
            "Target": {
                "populated_from": "Source",
                "permissible_value_derivations": {
                    "red": {"populated_from": ["light_red", "dark_red"]},
                },
            },
        },
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []


def test_pv_populated_from_scalar_validates():
    """Scalar populated_from on a PV deriv is accepted (wrapped to list)."""
    spec = {
        "enum_derivations": {
            "Target": {
                "populated_from": "Source",
                "permissible_value_derivations": {
                    "red": {"populated_from": "light_red"},
                },
            },
        },
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []


def test_pv_sources_only_is_deprecation_not_conflict():
    """Sources-only is a deprecation warning, not a conflict error."""
    spec = {
        "enum_derivations": {
            "Target": {
                "populated_from": "Source",
                "permissible_value_derivations": {
                    "red": {"sources": ["light_red", "dark_red"]},
                },
            },
        },
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []
    warnings = _warnings(msgs)
    assert any("sources" in m.message and "PermissibleValueDerivation" in m.path for m in warnings)


def test_pv_sources_and_populated_from_both_set_errors():
    """Setting both sources and populated_from on a PV deriv is an error."""
    spec = {
        "enum_derivations": {
            "Target": {
                "populated_from": "Source",
                "permissible_value_derivations": {
                    "red": {
                        "populated_from": ["light_red"],
                        "sources": ["dark_red"],
                    },
                },
            },
        },
    }
    msgs = validate_spec(spec)
    errors = _errors(msgs)
    assert any("both 'populated_from' and 'sources'" in m.message for m in errors)
    assert any("'red'" in m.message for m in errors)


# ---------------------------------------------------------------------------
# File-level validation against real trans-specs (structural only)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spec_file",
    sorted(EXAMPLE_DIR.rglob("*.transform.yaml")),
    ids=lambda p: str(p.relative_to(EXAMPLE_DIR)),
)
def test_validate_all_example_specs(spec_file):
    """All bundled example trans-specs pass structural validation."""
    msgs = validate_spec_file(spec_file)
    errors = _errors(msgs)
    assert errors == [], f"Validation errors in {spec_file.name}:\n" + "\n".join(str(e) for e in errors)


def test_validate_non_mapping_file(tmp_path):
    """A YAML file that is a list (not a mapping) reports an error."""
    f = tmp_path / "bad.yaml"
    f.write_text("- item1\n- item2\n")
    msgs = validate_spec_file(f)
    assert len(msgs) == 1
    assert msgs[0].severity == "error"
    assert "mapping" in msgs[0].message.lower()


# ---------------------------------------------------------------------------
# Unit tests for extract_expr_slot_references
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("str({age_in_years}) + ' years'", {"age_in_years"}),
        ("{x} + {y}", {"x", "y"}),
        ("x + y", {"x", "y"}),
        ("subject.id", {"subject"}),
        ("src.has_events", {"has_events"}),
        ("src.slot_a + src.slot_b", {"slot_a", "slot_b"}),
        ("case((x == '1', 'YES'), (True, 'NO'))", {"x"}),
        ("'hello'", set()),
        ("42", set()),
        ("True", set()),
        ("None", set()),
        ("NULL", set()),
        ("str(x)", {"x"}),
        ("strlen(name)", {"name"}),
        ("lookup(predicate)", {"lookup", "predicate"}),
    ],
    ids=lambda x: repr(x) if isinstance(x, str) else None,
)
def test_extract_expr_slot_references(expr, expected):
    """Expression slot reference extraction covers various patterns."""
    assert extract_expr_slot_references(expr) == expected


def test_extract_expr_multiline():
    """Multi-line expressions (asteval mode) are parsed correctly."""
    expr = """\
d_test = [x.important_event_date for x in src.has_important_life_events if str(x.event_name) == "PASSED_DRIVING_TEST"]
if len(d_test):
    target = d_test[0]
"""
    refs = extract_expr_slot_references(expr)
    assert "has_important_life_events" in refs
    # d_test and x are local variables (assignment target and comprehension
    # variable respectively) — they are filtered out by the bound-name logic.
    assert "d_test" not in refs
    assert "x" not in refs


def test_extract_expr_unparsable():
    """Completely unparsable expressions return empty set."""
    assert extract_expr_slot_references("{{{{") == set()


# ---------------------------------------------------------------------------
# Unit tests for validate_spec_semantics
# ---------------------------------------------------------------------------


def test_semantics_valid_target_class():
    """A class derivation matching a target schema class produces no errors."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {"Person": {"populated_from": "Person"}},
        }
    )
    msgs = validate_spec_semantics(spec, target_schema=str(PERSONINFO_SRC_SCHEMA))
    errors = _errors(msgs)
    assert errors == []


def test_semantics_invalid_target_class():
    """A class derivation with a typo in the target class name is an error."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {"PersonTypo": {"populated_from": "Person"}},
        }
    )
    msgs = validate_spec_semantics(spec, target_schema=str(PERSONINFO_SRC_SCHEMA))
    errors = _errors(msgs)
    assert len(errors) == 1
    assert "PersonTypo" in errors[0].message
    assert "not found in target schema" in errors[0].message


def test_semantics_invalid_source_class():
    """A populated_from referencing a nonexistent source class is an error."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {"Person": {"populated_from": "NonExistent"}},
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    errors = _errors(msgs)
    assert len(errors) == 1
    assert "NonExistent" in errors[0].message
    assert "not found in source schema" in errors[0].message


def test_semantics_valid_slot_derivation():
    """A slot derivation matching a target class slot produces no errors."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {"primary_email": None},
                },
            },
        }
    )
    msgs = validate_spec_semantics(
        spec,
        source_schema=str(PERSONINFO_SRC_SCHEMA),
        target_schema=str(PERSONINFO_SRC_SCHEMA),
    )
    errors = _errors(msgs)
    assert errors == []


def test_semantics_invalid_target_slot():
    """A slot derivation with a typo in the target slot name is an error."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {"naem": None},
                },
            },
        }
    )
    msgs = validate_spec_semantics(spec, target_schema=str(PERSONINFO_SRC_SCHEMA))
    errors = _errors(msgs)
    assert any("naem" in e.message for e in errors)


def test_semantics_invalid_populated_from_slot():
    """A slot populated_from referencing a nonexistent source slot is an error."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {
                        "primary_email": {"populated_from": "nonexistent_slot"},
                    },
                },
            },
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    errors = _errors(msgs)
    assert any("nonexistent_slot" in e.message for e in errors)


def test_semantics_expr_slot_reference_warning():
    """An expression referencing a slot not on the source class is a warning by default."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {
                        "primary_email": {"expr": "bogus_slot + '_suffix'"},
                    },
                },
            },
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    warnings = _warnings(msgs)
    assert any("bogus_slot" in w.message for w in warnings)
    assert _errors(msgs) == []


def test_semantics_expr_slot_reference_strict():
    """With strict=True, unresolved expression slot references become errors."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {
                        "primary_email": {"expr": "bogus_slot + '_suffix'"},
                    },
                },
            },
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA), strict=True)
    errors = _errors(msgs)
    assert any("bogus_slot" in e.message for e in errors)


def test_semantics_valid_expr_reference():
    """An expression referencing a real source slot produces no warnings."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {
                        "primary_email": {"expr": "str(age_in_years) + ' years'"},
                    },
                },
            },
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    expr_msgs = [m for m in msgs if "age_in_years" in m.message]
    assert expr_msgs == []


def test_semantics_join_alias_in_expr_no_warning():
    """Join aliases in expressions must not produce false-positive warnings.

    Regression: previously, an expression like ``{demographics.age}`` where
    ``demographics`` is a ``joins:`` alias (not a source-class slot) would
    fire an "Expression references 'demographics' which is not a slot..."
    warning. Join aliases should be excluded from expression-reference
    validation since they refer to joined tables.
    """
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "joins": {
                        "demographics": {"join_on": "id"},
                    },
                    "slot_derivations": {
                        "primary_email": {"expr": "{demographics.age_at_exam}"},
                    },
                },
            },
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    bogus = [m for m in msgs if "demographics" in m.message and "not a slot" in m.message]
    assert bogus == [], f"join alias 'demographics' should not be flagged: {bogus}"


def test_semantics_enum_derivation_valid():
    """A valid enum derivation produces no errors."""
    spec = normalize_spec_dict(
        {
            "enum_derivations": {
                "FamilialRelationshipType": {"populated_from": "FamilialRelationshipType"},
            },
        }
    )
    msgs = validate_spec_semantics(
        spec,
        source_schema=str(PERSONINFO_SRC_SCHEMA),
        target_schema=str(PERSONINFO_SRC_SCHEMA),
    )
    errors = _errors(msgs)
    assert errors == []


def test_semantics_enum_derivation_invalid_target():
    """An enum derivation with a nonexistent target enum is an error."""
    spec = normalize_spec_dict(
        {
            "enum_derivations": {
                "NonExistentEnum": {"populated_from": "FamilialRelationshipType"},
            },
        }
    )
    msgs = validate_spec_semantics(spec, target_schema=str(PERSONINFO_SRC_SCHEMA))
    errors = _errors(msgs)
    assert any("NonExistentEnum" in e.message for e in errors)


def test_semantics_enum_derivation_invalid_source():
    """An enum populated_from referencing a nonexistent source enum is an error."""
    spec = normalize_spec_dict(
        {
            "enum_derivations": {
                "FamilialRelationshipType": {"populated_from": "NoSuchEnum"},
            },
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    errors = _errors(msgs)
    assert any("NoSuchEnum" in e.message for e in errors)


def test_semantics_required_slot_warning():
    """A required target slot with no derivation produces a warning."""
    # FamilialRelationship has required slots: 'type' and 'related_to'
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "FamilialRelationship": {
                    "populated_from": "FamilialRelationship",
                    "slot_derivations": {"type": None},
                    # 'related_to' is required but not derived
                },
            },
        }
    )
    msgs = validate_spec_semantics(spec, target_schema=str(PERSONINFO_SRC_SCHEMA))
    warnings = _warnings(msgs)
    assert any("related_to" in w.message and "required" in w.message.lower() for w in warnings)


def test_semantics_auto_detect_schemas():
    """Schemas are auto-detected from the spec's source_schema/target_schema fields."""
    msgs = validate_spec_file(str(FLATTENING_TR))
    # FLATTENING_TR uses non-resolvable placeholder identifiers (s1/s2) for
    # source_schema/target_schema, so auto-detection finds nothing to load
    # and semantic validation is skipped — only structural checks run.
    errors = _errors(msgs)
    assert errors == []


def test_semantics_flattening_example():
    """The flattening example validates cleanly with both schemas."""
    msgs = validate_spec_file(
        str(FLATTENING_TR),
        source_schema=str(FLATTENING_SRC_SCHEMA),
        target_schema=str(FLATTENING_TGT_SCHEMA),
    )
    errors = _errors(msgs)
    assert errors == [], "\n".join(str(e) for e in errors)


def test_semantics_no_schemas_no_semantic_messages():
    """Without schemas, only structural validation runs."""
    spec = {
        "class_derivations": {"Foo": {"populated_from": "Bar"}},
    }
    msgs = validate_spec(spec)
    assert msgs == []


def test_validation_message_str():
    """ValidationMessage.__str__ formats correctly."""
    msg = ValidationMessage(severity="error", path="class_derivations[Foo]", message="not found")
    assert str(msg) == "class_derivations[Foo]: [error] not found"


# ---------------------------------------------------------------------------
# Deprecation check
# ---------------------------------------------------------------------------


def test_check_deprecated_fields_sources_on_class_derivation():
    """``sources`` on a ClassDerivation produces a deprecation message."""
    from linkml_map.validator import check_deprecated_fields

    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {"populated_from": "Person", "sources": ["LegacyPerson"]},
            },
        }
    )
    msgs = check_deprecated_fields(spec)
    assert len(msgs) == 1
    assert msgs[0].severity == "warning"
    assert msgs[0].category == "deprecated"
    assert "ClassDerivation" in msgs[0].message
    assert "sources" in msgs[0].message
    assert "Person" in msgs[0].message


def test_check_deprecated_fields_derived_from_on_slot_derivation():
    """``derived_from`` on a SlotDerivation produces a deprecation message."""
    from linkml_map.validator import check_deprecated_fields

    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {
                        "full_name": {
                            "expr": "{given_name} + ' ' + {family_name}",
                            "derived_from": ["given_name", "family_name"],
                        }
                    },
                },
            },
        }
    )
    msgs = check_deprecated_fields(spec)
    assert len(msgs) == 1
    assert msgs[0].severity == "warning"
    assert msgs[0].category == "deprecated"
    assert "derived_from" in msgs[0].message
    assert "full_name" in msgs[0].message


def test_check_deprecated_fields_collapses_per_derivation_type():
    """Multiple sources of the same kind collapse to one message per type."""
    from linkml_map.validator import check_deprecated_fields

    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "A": {"populated_from": "A", "sources": ["X"]},
                "B": {"populated_from": "B", "sources": ["Y"]},
            },
        }
    )
    msgs = check_deprecated_fields(spec)
    # Both ClassDerivations collapsed into a single ClassDerivation message.
    assert len(msgs) == 1
    assert "2 ClassDerivation(s)" in msgs[0].message


def test_check_deprecated_fields_truncates_long_lists():
    """When more than 5 derivations have a deprecated field, names are truncated."""
    from linkml_map.validator import check_deprecated_fields

    cds = {f"C{i}": {"populated_from": f"C{i}", "sources": ["X"]} for i in range(7)}
    spec = normalize_spec_dict({"class_derivations": cds})
    msgs = check_deprecated_fields(spec)
    assert len(msgs) == 1
    assert "(and 2 more)" in msgs[0].message


def test_check_deprecated_fields_clean_spec_returns_empty():
    """A spec with no deprecated field usage produces no messages."""
    from linkml_map.validator import check_deprecated_fields

    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Person": {
                    "populated_from": "Person",
                    "slot_derivations": {"name": {"populated_from": "name"}},
                },
            },
        }
    )
    msgs = check_deprecated_fields(spec)
    assert msgs == []


def test_validate_spec_includes_deprecation_messages():
    """``validate_spec`` surfaces deprecation messages alongside other findings."""
    spec = {
        "class_derivations": {
            "Person": {"populated_from": "Person", "sources": ["LegacyPerson"]},
        },
    }
    msgs = validate_spec(spec)
    deprecations = [m for m in msgs if m.category == "deprecated"]
    assert len(deprecations) == 1
    assert "sources" in deprecations[0].message
