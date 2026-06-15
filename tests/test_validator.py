"""Tests for transformation specification validation."""

import textwrap

import pytest
from linkml_runtime import SchemaView

from linkml_map.validator import (
    ValidationMessage,
    extract_expr_attribute_references,
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


def _infos(messages: list[ValidationMessage]) -> list[ValidationMessage]:
    return [m for m in messages if m.severity == "info"]


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


def test_pv_sources_in_compact_key_list_form_detected():
    """Compact-key list-form PV derivs (`[{name: {sources: [...]}}]`) are scanned.

    The SHAPE phase expands compact-key list items before the SCAN runs, so
    the deprecation warning fires end-to-end through ``validate_spec``.
    """
    spec = {
        "enum_derivations": {
            "Target": {
                "populated_from": "Source",
                "permissible_value_derivations": [
                    {"red": {"sources": ["light_red", "dark_red"]}},
                ],
            },
        },
    }
    msgs = validate_spec(spec)
    assert _errors(msgs) == []
    warnings = _warnings(msgs)
    assert any("sources" in m.message and "PermissibleValueDerivation" in m.path for m in warnings), (
        f"Expected deprecation warning for compact-key list PV; got {warnings}"
    )


def test_pv_populated_from_explicit_none_is_stripped():
    """`populated_from: null` (explicit YAML None) is dropped during normalize."""
    raw = {
        "enum_derivations": {
            "Target": {
                "populated_from": "Source",
                "permissible_value_derivations": {
                    "red": {"populated_from": None},
                },
            },
        },
    }
    normalized = normalize_spec_dict(raw)
    # After normalize, the PV's populated_from key has been removed; pydantic
    # will fill in the default factory ([]) when the model is built.
    eds = normalized["enum_derivations"]
    pvds = eds["Target"]["permissible_value_derivations"]
    pvd = pvds["red"] if isinstance(pvds, dict) else next(iter(pvds))
    assert "populated_from" not in pvd


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


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("{demographics.age}", {"demographics": {"age"}}),
        ("{a.x} + {a.y}", {"a": {"x", "y"}}),
        ("{a.x} + {b.y}", {"a": {"x"}, "b": {"y"}}),
        ("src.foo", {}),  # src.* handled by slot ref extractor
        ("plain_var", {}),
        ("'hello'", {}),
    ],
    ids=lambda x: repr(x) if isinstance(x, str) else None,
)
def test_extract_expr_attribute_references(expr, expected):
    """Attribute reference extraction covers cross-table dot notation."""
    assert extract_expr_attribute_references(expr) == expected


def test_extract_expr_attribute_references_unparsable():
    """Unparsable expressions yield an empty mapping, not a crash."""
    assert extract_expr_attribute_references("{{{{") == {}


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


# ---------------------------------------------------------------------------
# Nested cross-table class_derivation validation (#211)
# ---------------------------------------------------------------------------


JOINABLE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/joinable
    name: joinable
    prefixes:
      linkml: https://w3id.org/linkml/
    default_prefix: joinable
    default_range: string
    imports:
      - linkml:types

    classes:
      Measurement:
        attributes:
          id:
            identifier: true
          subject_id:
          method:
      Reading:
        attributes:
          id:
            identifier: true
          subject_id:
          score:
            range: float
""")


NO_OVERLAP_SCHEMA = textwrap.dedent("""\
    id: https://example.org/no-overlap
    name: no_overlap
    prefixes:
      linkml: https://w3id.org/linkml/
    default_prefix: no_overlap
    default_range: string
    imports:
      - linkml:types

    classes:
      Measurement:
        attributes:
          id:
            identifier: true
          method:
      Reading:
        attributes:
          reading_id:
            identifier: true
          score:
""")


AMBIGUOUS_SCHEMA = textwrap.dedent("""\
    id: https://example.org/ambiguous
    name: ambiguous
    prefixes:
      linkml: https://w3id.org/linkml/
    default_prefix: ambiguous
    default_range: string
    imports:
      - linkml:types

    classes:
      Measurement:
        attributes:
          id:
            identifier: true
          subject_id:
          sample_id:
          method:
      Reading:
        attributes:
          id:
            identifier: true
          subject_id:
          sample_id:
          score:
""")


THREE_TABLE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/three-table
    name: three_table
    prefixes:
      linkml: https://w3id.org/linkml/
    default_prefix: three_table
    default_range: string
    imports:
      - linkml:types

    classes:
      Outer:
        attributes:
          id:
            identifier: true
          shared_om:
      Middle:
        attributes:
          mid_id:
            identifier: true
          shared_om:
          shared_mi:
      Inner:
        attributes:
          inner_id:
            identifier: true
          shared_mi:
          payload:
""")


def _nested_spec(outer_pf: str, inner_pf: str, joins: dict | None = None) -> dict:
    """Build a normalized 2-level nested spec with the given populated_from values."""
    inner_cd: dict = {
        "Inner": {
            "populated_from": inner_pf,
            "slot_derivations": {"score": None},
        }
    }
    outer_cd: dict = {
        "populated_from": outer_pf,
        "slot_derivations": {
            "observation": {"class_derivations": [inner_cd]},
        },
    }
    if joins is not None:
        outer_cd["joins"] = joins
    return normalize_spec_dict({"class_derivations": {"Outer": outer_cd}})


def _nested_path_segment(path: str) -> bool:
    return "Inner" in path and "Outer" in path


def test_nested_cd_same_populated_from_no_message():
    """Nested CD with the same populated_from as parent emits no cross-table message."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(outer_pf="Measurement", inner_pf="Measurement")
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    cross_msgs = [m for m in msgs if "implicit join" in m.message or "no implicit join" in m.message]
    assert cross_msgs == []


def test_nested_cd_explicit_join_no_message():
    """Nested CD with an explicit joins: entry covering its source emits no cross-table message."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {"join_on": "subject_id"}},
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    cross_msgs = [m for m in msgs if "implicit join" in m.message or "no implicit join" in m.message]
    assert cross_msgs == []


def test_nested_cd_implicit_join_emits_info():
    """Synthesizable implicit join emits an INFO with the column name."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(outer_pf="Measurement", inner_pf="Reading")
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    infos = _infos(msgs)
    assert len(infos) == 1
    assert "implicit join" in infos[0].message
    assert "subject_id" in infos[0].message
    assert _nested_path_segment(infos[0].path)


def test_nested_cd_no_overlap_emits_warning():
    """No shared columns between parent and nested tables emits a WARNING (closes #211)."""
    sv = SchemaView(NO_OVERLAP_SCHEMA)
    spec = _nested_spec(outer_pf="Measurement", inner_pf="Reading")
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "no implicit join" in m.message]
    assert len(warnings) == 1
    assert "no columns are shared" in warnings[0].message
    assert _nested_path_segment(warnings[0].path)


def test_nested_cd_ambiguous_emits_warning():
    """Multiple non-identifier common columns yield an 'ambiguous candidates' WARNING."""
    sv = SchemaView(AMBIGUOUS_SCHEMA)
    spec = _nested_spec(outer_pf="Measurement", inner_pf="Reading")
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "no implicit join" in m.message]
    assert len(warnings) == 1
    assert "multiple candidate" in warnings[0].message
    assert "subject_id" in warnings[0].message
    assert "sample_id" in warnings[0].message


def test_nested_cd_three_level_walks_each_boundary():
    """Cross-table check fires at every parent→child boundary in deeply nested specs."""
    sv = SchemaView(THREE_TABLE_SCHEMA)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Outer": {
                    "populated_from": "Outer",
                    "slot_derivations": {
                        "mid": {
                            "class_derivations": [
                                {
                                    "Middle": {
                                        "populated_from": "Middle",
                                        "slot_derivations": {
                                            "inner": {
                                                "class_derivations": [
                                                    {
                                                        "Inner": {
                                                            "populated_from": "Inner",
                                                        }
                                                    }
                                                ]
                                            },
                                        },
                                    }
                                }
                            ]
                        }
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    infos = _infos(msgs)
    # Two boundaries: Outer↔Middle (shared_om) and Middle↔Inner (shared_mi).
    assert len(infos) == 2
    keys = sorted(m.message for m in infos)
    assert any("shared_om" in m for m in keys)
    assert any("shared_mi" in m for m in keys)
    # Paths reflect the nesting depth.
    assert any("Middle" in m.path and "Outer" in m.path for m in infos)
    assert any("Inner" in m.path and "Middle" in m.path for m in infos)


def test_nested_cd_issue_211_regression():
    """Reproduction of the #211 ARIC spirometry shape.

    Two parent/child tables share a single subject identifier column. The
    spec has no explicit joins: block. Validator emits an INFO indicating
    the implicit join will synthesize at runtime — no silent null hazard.
    """
    schema = textwrap.dedent("""\
        id: https://example.org/aric-211
        name: aric_211
        prefixes:
          linkml: https://w3id.org/linkml/
        default_prefix: aric_211
        default_range: string
        imports:
          - linkml:types

        classes:
          pht006467:
            attributes:
              dbGaP_subject_id:
                identifier: true
              phv00297546:
              phv00297568:
                range: float
          pht012814:
            attributes:
              dbGaP_subject_id:
              phv00512050:
                range: integer
              phv00512107:
                range: float
    """)
    sv = SchemaView(schema)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "MeasurementObservationSet": {
                    "populated_from": "pht006467",
                    "slot_derivations": {
                        "observations": {
                            "class_derivations": [
                                {
                                    "MeasurementObservation_inner": {
                                        "populated_from": "pht012814",
                                        "slot_derivations": {
                                            "value_decimal": {"expr": "{pht012814.phv00512107}"},
                                        },
                                    }
                                }
                            ]
                        }
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    infos = _infos(msgs)
    assert len(infos) == 1
    assert "implicit join" in infos[0].message
    assert "dbGaP_subject_id" in infos[0].message


def test_nested_cd_expr_attribute_validated_against_joined_class():
    """Expression refs like {joined.field} validate against the joined class's slots (#213 stretch)."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Outer": {
                    "populated_from": "Measurement",
                    "slot_derivations": {
                        "observation": {"class_derivations": [{"Inner": {"populated_from": "Reading"}}]},
                        "computed": {"expr": "{Reading.score}"},  # valid slot on Reading
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    expr_msgs = [m for m in msgs if "Reading.score" in m.message]
    assert expr_msgs == []


def test_nested_cd_expr_attribute_unknown_field_warns():
    """A {joined.bogus} ref on a known joined class warns when the field doesn't exist."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Outer": {
                    "populated_from": "Measurement",
                    "slot_derivations": {
                        "observation": {"class_derivations": [{"Inner": {"populated_from": "Reading"}}]},
                        "computed": {"expr": "{Reading.bogus_field}"},
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "Reading.bogus_field" in m.message and "joined class" in m.message]
    assert len(warnings) == 1


def test_nested_cd_expr_attribute_explicit_join_alias_validated():
    """{alias.field} on an explicit joins: alias also validates against the joined class."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Outer": {
                    "populated_from": "Measurement",
                    "joins": {
                        "readings": {"join_on": "subject_id", "class_named": "Reading"},
                    },
                    "slot_derivations": {
                        "computed": {"expr": "{readings.bogus_field}"},
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "readings.bogus_field" in m.message and "joined class" in m.message]
    assert len(warnings) == 1


def test_nested_cd_no_source_schema_no_cross_table_messages():
    """With no source schema, cross-table checks are skipped (can't predict)."""
    spec = _nested_spec(outer_pf="Measurement", inner_pf="Reading")
    msgs = validate_spec_semantics(spec, target_schema=str(PERSONINFO_SRC_SCHEMA))
    cross = [m for m in msgs if "implicit join" in m.message]
    assert cross == []


def test_identity_case_parent_cd_validated_against_runtime():
    """A parent CD with no populated_from uses its name as the source class.

    Runtime falls back to ``parent_class_deriv.populated_from or
    parent_class_deriv.name`` (see ObjectTransformer._derive_nested_objects),
    so the validator must too — otherwise nested cross-table refs from an
    identity-style outer CD silently pass.
    """
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                # Outer "Measurement" CD — no populated_from, identity case.
                "Measurement": {
                    "slot_derivations": {
                        "observation": {
                            "class_derivations": [{"Inner": {"populated_from": "Reading"}}],
                        },
                        "computed": {"expr": "{Reading.bogus_field}"},
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    # Cross-table check should fire (Measurement → Reading is a real boundary).
    infos = [m for m in _infos(msgs) if "implicit join" in m.message]
    assert len(infos) == 1
    assert "subject_id" in infos[0].message
    # Attribute ref against Reading should be validated — bogus_field caught.
    attr_warnings = [m for m in _warnings(msgs) if "Reading.bogus_field" in m.message]
    assert len(attr_warnings) == 1


def test_nested_cd_without_populated_from_inherits_parent_source():
    """A nested CD without populated_from inherits the parent's effective source.

    Runtime's _derive_nested_objects feeds the parent's row through to a
    nested CD that omits populated_from, so the validator must resolve
    ``source_class_slots`` against the parent's effective source class
    (``parent.populated_from or parent.name``). Otherwise bogus slot refs
    inside the nested CD silently pass semantic validation.
    """
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Measurement": {
                    "populated_from": "Measurement",
                    "slot_derivations": {
                        "observation": {
                            # Nested CD inherits parent's source (Measurement) — no populated_from.
                            "class_derivations": [
                                {
                                    "Inner": {
                                        "slot_derivations": {
                                            "x": {"populated_from": "bogus_slot"},
                                        },
                                    }
                                }
                            ],
                        },
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    errors = [m for m in msgs if m.severity == "error" and "bogus_slot" in m.message]
    assert len(errors) == 1


# ---------------------------------------------------------------------------
# is_a / mixins resolution (#219, Option C)
# ---------------------------------------------------------------------------


def test_is_a_resolves_via_spec_internal_pool():
    """is_a referencing another top-level class_derivation in the spec is valid."""
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Entity": None,
                "Agent": {"is_a": "Entity", "populated_from": "Person"},
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    inheritance_errors = [m for m in _errors(msgs) if "does not resolve" in m.message]
    assert inheritance_errors == []


def test_is_a_resolves_via_target_schema():
    """is_a referencing a target schema class name (not in spec pool) is valid."""
    target_schema = textwrap.dedent("""\
        id: https://example.org/agent-target
        name: agent_target
        prefixes:
          linkml: https://w3id.org/linkml/
        default_prefix: agent_target
        default_range: string
        imports:
          - linkml:types
        classes:
          Entity:
            description: Target-schema base class
          Agent:
            is_a: Entity
    """)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Agent": {"is_a": "Entity", "populated_from": "Person"},
            }
        }
    )
    target_sv = SchemaView(target_schema)
    msgs = validate_spec_semantics(spec, target_schemaview=target_sv)
    inheritance_errors = [m for m in _errors(msgs) if "does not resolve" in m.message]
    assert inheritance_errors == []


def test_is_a_unresolved_emits_error():
    """is_a that resolves to neither pool nor target schema is an error (#219)."""
    target_schema = textwrap.dedent("""\
        id: https://example.org/empty-target
        name: empty_target
        prefixes:
          linkml: https://w3id.org/linkml/
        default_prefix: empty_target
        default_range: string
        imports:
          - linkml:types
        classes:
          Agent:
    """)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Agent": {"is_a": "TotallyMadeUpName", "populated_from": "Person"},
            }
        }
    )
    target_sv = SchemaView(target_schema)
    msgs = validate_spec_semantics(spec, target_schemaview=target_sv)
    errors = [m for m in _errors(msgs) if "TotallyMadeUpName" in m.message]
    assert len(errors) == 1
    assert "is_a" in errors[0].message
    assert "does not resolve" in errors[0].message


def test_mixins_each_entry_resolved_independently():
    """mixins is a list; each entry resolves independently against pool + target."""
    target_schema = textwrap.dedent("""\
        id: https://example.org/mixins-target
        name: mixins_target
        prefixes:
          linkml: https://w3id.org/linkml/
        default_prefix: mixins_target
        default_range: string
        imports:
          - linkml:types
        classes:
          NamedThing:
          Agent:
    """)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "InternalMixin": None,
                "Agent": {
                    "mixins": ["InternalMixin", "NamedThing", "BogusMixin"],
                    "populated_from": "Person",
                },
            }
        }
    )
    target_sv = SchemaView(target_schema)
    msgs = validate_spec_semantics(spec, target_schemaview=target_sv)
    errors = [m for m in _errors(msgs) if "does not resolve" in m.message]
    assert len(errors) == 1
    assert "BogusMixin" in errors[0].message
    assert "mixins" in errors[0].message


def test_is_a_and_mixins_both_validated():
    """Both is_a and mixins emit errors for unresolved references on the same CD."""
    target_schema = textwrap.dedent("""\
        id: https://example.org/dual
        name: dual
        prefixes:
          linkml: https://w3id.org/linkml/
        default_prefix: dual
        default_range: string
        imports:
          - linkml:types
        classes:
          Agent:
    """)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Agent": {
                    "is_a": "MissingParent",
                    "mixins": ["MissingMixin"],
                    "populated_from": "Person",
                }
            }
        }
    )
    target_sv = SchemaView(target_schema)
    msgs = validate_spec_semantics(spec, target_schemaview=target_sv)
    errors = [m for m in _errors(msgs) if "does not resolve" in m.message]
    assert len(errors) == 2
    field_labels = {("is_a" if "is_a" in e.message else "mixins") for e in errors}
    assert field_labels == {"is_a", "mixins"}


def test_personinfo_to_agent_fixture_inheritance_resolves():
    """The personinfo-to-agent fixture's Agent.is_a: Entity must resolve via pool-1."""
    from pathlib import Path

    fixture = Path(EXAMPLE_DIR) / "personinfo_basic" / "transform" / "personinfo-to-agent.transform.yaml"
    msgs = validate_spec_file(fixture)
    inheritance_errors = [m for m in _errors(msgs) if "does not resolve" in m.message]
    assert inheritance_errors == []


def test_is_a_unresolved_skipped_when_no_target_schema():
    """Without target_sv, an is_a miss against the spec pool alone is not an error.

    The reference might be a valid target-schema class name; we can't tell
    without the target schema, so we don't error on a half-checked pool.
    """
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Agent": {"is_a": "TotallyMadeUpName", "populated_from": "Person"},
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schema=str(PERSONINFO_SRC_SCHEMA))
    inheritance_errors = [m for m in _errors(msgs) if "does not resolve" in m.message]
    assert inheritance_errors == []


# ---------------------------------------------------------------------------
# Incomplete-join-spec detection on cross-table boundaries
# ---------------------------------------------------------------------------


def test_cross_table_empty_explicit_join_emits_warning():
    """An explicit joins: entry that's empty fails at runtime — surface it here."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {}},
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "missing keys" in m.message]
    assert len(warnings) == 1
    assert "Reading" in warnings[0].message


def test_cross_table_source_lookup_keys_satisfy_join():
    """A join spec using source_key + lookup_key (not join_on) is valid."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {"source_key": "subject_id", "lookup_key": "subject_id"}},
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    incomplete = [m for m in _warnings(msgs) if "missing keys" in m.message]
    assert incomplete == []


def test_cross_table_source_key_only_emits_warning():
    """source_key without lookup_key (and no join_on) fails — both keys required."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {"source_key": "subject_id"}},
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "missing keys" in m.message]
    assert len(warnings) == 1


def test_cross_table_join_on_typo_emits_warning_per_side():
    """A join_on key that exists on neither side emits a warning naming each class."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {"join_on": "subjet_id"}},  # typo
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "'join_on=subjet_id' is not a slot" in m.message]
    assert len(warnings) == 2
    classes_named = {w.message.split("source class '")[1].split("'")[0] for w in warnings}
    assert classes_named == {"Measurement", "Reading"}


def test_cross_table_join_on_one_sided_emits_single_warning():
    """A join_on key present on parent but absent on nested fires only for the nested side."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {"join_on": "method"}},  # method exists on Measurement, not Reading
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "'join_on=method' is not a slot" in m.message]
    assert len(warnings) == 1
    assert "'Reading'" in warnings[0].message


def test_cross_table_source_key_typo_emits_warning():
    """A source_key absent on the parent class emits a warning."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {"source_key": "subjet_id", "lookup_key": "subject_id"}},
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "'source_key=subjet_id' is not a slot" in m.message]
    assert len(warnings) == 1
    assert "'Measurement'" in warnings[0].message


def test_cross_table_lookup_key_typo_emits_warning():
    """A lookup_key absent on the nested class emits a warning."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = _nested_spec(
        outer_pf="Measurement",
        inner_pf="Reading",
        joins={"Reading": {"source_key": "subject_id", "lookup_key": "subjet_id"}},
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "'lookup_key=subjet_id' is not a slot" in m.message]
    assert len(warnings) == 1
    assert "'Reading'" in warnings[0].message


# ---------------------------------------------------------------------------
# Joined-class error message includes resolved class name when aliased
# ---------------------------------------------------------------------------


def test_joined_class_attr_error_uses_class_named_when_aliased():
    """Error message names the actual joined class, not just the alias, when class_named is set."""
    sv = SchemaView(JOINABLE_SCHEMA)
    spec = normalize_spec_dict(
        {
            "class_derivations": {
                "Outer": {
                    "populated_from": "Measurement",
                    "joins": {
                        "readings": {"join_on": "subject_id", "class_named": "Reading"},
                    },
                    "slot_derivations": {
                        "computed": {"expr": "{readings.bogus_field}"},
                    },
                }
            }
        }
    )
    msgs = validate_spec_semantics(spec, source_schemaview=sv)
    warnings = [m for m in _warnings(msgs) if "readings.bogus_field" in m.message]
    assert len(warnings) == 1
    msg = warnings[0].message
    assert "joined class 'Reading'" in msg
    assert "alias 'readings'" in msg
