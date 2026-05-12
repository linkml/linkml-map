"""Tests for strict-mode expression evaluation (issue #213).

In non-strict mode the evaluator preserves SQL-style null propagation but
emits a warning when an expression references a name that is not a slot
on the source class. In strict mode the same condition raises
``TransformationError``.

A schema-declared slot that is absent from the current row must still
resolve to ``None`` in both modes — that case is a real SQL null, not
a typo.
"""

import logging

import pytest
import yaml
from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime import SchemaView

from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer


def _build_schemas() -> tuple:
    """Source has Person(id, age, score); target has Agent(name)."""
    sb_source = SchemaBuilder()
    sb_source.add_slot("id", range="string")
    sb_source.add_slot("age", range="integer")
    sb_source.add_slot("score", range="integer")
    sb_source.add_class("Person", slots=["id", "age", "score"])
    sb_source.add_defaults()

    sb_target = SchemaBuilder()
    sb_target.add_slot("name", range="string")
    sb_target.add_class("Agent", slots=["name"])
    sb_target.add_defaults()

    return sb_source.schema, sb_target.schema


def _make_transformer(transform_spec: dict, *, strict: bool) -> ObjectTransformer:
    """Build a transformer with the given strict flag and inline spec."""
    source_schema, target_schema = _build_schemas()
    transformer = ObjectTransformer(strict=strict)
    transformer.source_schemaview = SchemaView(source_schema)
    transformer.target_schemaview = SchemaView(target_schema)
    transformer.create_transformer_specification(transform_spec)
    return transformer


TYPO_SPEC = yaml.safe_load(
    "class_derivations:\n"
    "  Agent:\n"
    "    populated_from: Person\n"
    "    slot_derivations:\n"
    "      name:\n"
    '        expr: "{scroe}"\n'  # codespell:ignore
)


VALID_SPEC = yaml.safe_load("""
class_derivations:
  Agent:
    populated_from: Person
    slot_derivations:
      name:
        expr: "str({score})"
""")


def test_typo_strict_raises() -> None:
    """Strict mode raises TransformationError when an expression references a non-slot.

    The raw ``NameError`` from ``_eval_name`` is wrapped by
    ``_slot_error_context`` so the surfaced exception carries class /
    slot / source-row context for diagnostics.
    """
    transformer = _make_transformer(TYPO_SPEC, strict=True)
    with pytest.raises(TransformationError, match="scroe") as exc_info:  # codespell:ignore
        transformer.map_object({"id": "p1", "age": 30, "score": 5}, source_type="Person")
    assert exc_info.value.class_derivation_name == "Agent"
    assert exc_info.value.slot_derivation_name == "name"


def test_typo_non_strict_warns_and_returns_none(caplog: pytest.LogCaptureFixture) -> None:
    """Non-strict mode keeps the existing return-None behavior but logs a warning."""
    transformer = _make_transformer(TYPO_SPEC, strict=False)
    with caplog.at_level(logging.WARNING, logger="linkml_map.utils.eval_utils"):
        result = transformer.map_object({"id": "p1", "age": 30, "score": 5}, source_type="Person")
    assert result == {"name": None}
    assert any("scroe" in rec.message for rec in caplog.records)  # codespell:ignore


@pytest.mark.parametrize("strict", [True, False])
def test_schema_slot_with_null_value_resolves_to_none(strict: bool) -> None:
    """Slot is in the schema, value is None on this row → expression resolves to None."""
    transformer = _make_transformer(VALID_SPEC, strict=strict)
    result = transformer.map_object({"id": "p1", "age": 30, "score": None}, source_type="Person")
    assert result == {"name": None}


@pytest.mark.parametrize("strict", [True, False])
def test_schema_slot_absent_from_row_resolves_to_none(strict: bool) -> None:
    """Slot is declared on the source class but missing from this row → None (SQL null).

    This is the key distinction the fix introduces: a schema-declared
    slot absent from the row is a legitimate null, while a name that
    is not a slot at all is a typo. Both must behave correctly in
    strict mode.
    """
    transformer = _make_transformer(VALID_SPEC, strict=strict)
    result = transformer.map_object({"id": "p1", "age": 30}, source_type="Person")
    assert result == {"name": None}


def test_valid_slot_resolves_in_strict_mode() -> None:
    """A valid bare-name reference works in strict mode."""
    transformer = _make_transformer(VALID_SPEC, strict=True)
    result = transformer.map_object({"id": "p1", "age": 30, "score": 5}, source_type="Person")
    assert result == {"name": "5"}


def test_default_strict_is_false() -> None:
    """Default behavior is non-strict to preserve backward compatibility."""
    transformer = ObjectTransformer()
    assert transformer.strict is False


def test_non_strict_warning_dedupes_across_rows(caplog: pytest.LogCaptureFixture) -> None:
    """Each unique unbound name should warn once per transform run, not once per row.

    Without dedup, a typo in a spec used against a 10M-row dataset
    produces 10M log lines for one underlying problem.
    """
    transformer = _make_transformer(TYPO_SPEC, strict=False)
    rows = [
        {"id": "p1", "age": 30, "score": 5},
        {"id": "p2", "age": 31, "score": 6},
        {"id": "p3", "age": 32, "score": 7},
    ]
    with caplog.at_level(logging.WARNING, logger="linkml_map.utils.eval_utils"):
        for row in rows:
            transformer.map_object(row, source_type="Person")

    typo_warnings = [rec for rec in caplog.records if "scroe" in rec.message]  # codespell:ignore
    assert len(typo_warnings) == 1, (
        f"Expected one warning for the typo across {len(rows)} rows, got {len(typo_warnings)}"
    )
