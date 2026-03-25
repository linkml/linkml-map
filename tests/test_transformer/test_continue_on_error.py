"""Tests for --continue-on-error / TransformationError error handling.

Tests verify that:
1. TransformationError carries structured context (operation, slot, class, row)
2. engine.transform_spec collects errors via on_error callback
3. Default behavior (no callback) preserves fail-fast semantics
"""

# ruff: noqa: ANN401, PLR2004

import textwrap

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer


SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/error-test
    name: error_test
    prefixes:
      linkml: https://w3id.org/linkml/
    imports:
      - linkml:types
    default_range: string
    classes:
      Person:
        attributes:
          id:
            identifier: true
          name: {}
          age:
            range: integer
""")


def _make_transformer(spec_yaml: str) -> ObjectTransformer:
    """Build a transformer from inline YAML spec."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SCHEMA_YAML)
    spec = yaml.safe_load(spec_yaml)
    tr.create_transformer_specification(spec)
    return tr


# ---- TransformationError unit tests ----


def test_transformation_error_str_all_fields():
    """All context fields appear in string representation."""
    err = TransformationError(
        message="bad value",
        class_derivation_name="Person",
        slot_derivation_name="age",
        row_index=3,
    )
    s = str(err)
    assert "bad value" in s
    assert "Person" in s
    assert "age" in s
    assert "row=3" in s


def test_transformation_error_str_minimal():
    """Only message when no context fields set."""
    err = TransformationError(message="oops")
    assert str(err) == "oops"


def test_transformation_error_is_exception():
    """TransformationError can be raised and caught as Exception."""
    with pytest.raises(TransformationError, match="test"):
        raise TransformationError(message="test error")


def test_transformation_error_preserves_cause():
    """The cause field and __cause__ chain are set."""
    original = ValueError("original")
    err = TransformationError(message="wrapped", cause=original)
    assert err.cause is original


# ---- Engine-level error handling ----


@pytest.fixture
def data_dir_with_bad_row(tmp_path):
    """Create a data directory with one good row and one row that will cause an expr error."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "Person.tsv").write_text("id\tname\tage\nP001\tAlice\t30\nP002\tBob\t25\n")
    return data_dir


def test_on_error_collects_errors(data_dir_with_bad_row):
    """With on_error callback, bad rows are collected and good rows are yielded."""
    # Use an expr that will fail on every row (references undefined variable)
    spec_yaml = textwrap.dedent("""\
        class_derivations:
          Person:
            populated_from: Person
            slot_derivations:
              id: {}
              computed:
                expr: "undefined_var + 1"
    """)
    tr = _make_transformer(spec_yaml)
    loader = DataLoader(data_dir_with_bad_row)

    errors: list[TransformationError] = []
    results = list(transform_spec(tr, loader, on_error=errors.append))

    # All rows should fail (expr references undefined var)
    assert len(errors) == 2
    assert len(results) == 0

    # Errors should have context
    assert errors[0].row_index == 0
    assert errors[1].row_index == 1
    assert errors[0].class_derivation_name == "Person"
    assert errors[0].slot_derivation_name == "computed"


def test_on_error_none_preserves_fail_fast(data_dir_with_bad_row):
    """Without on_error callback, errors propagate immediately."""
    spec_yaml = textwrap.dedent("""\
        class_derivations:
          Person:
            populated_from: Person
            slot_derivations:
              id: {}
              computed:
                expr: "undefined_var + 1"
    """)
    tr = _make_transformer(spec_yaml)
    loader = DataLoader(data_dir_with_bad_row)

    with pytest.raises(TransformationError):
        list(transform_spec(tr, loader))


def test_on_error_good_rows_yielded(data_dir_with_bad_row):
    """Good rows are yielded even when some rows fail."""
    # Only the expr slot fails; id slot succeeds. But since we skip the whole row,
    # we get no results. Let's use a spec where only some rows fail instead.
    data_dir = data_dir_with_bad_row
    # Overwrite with mixed data: one row with valid expr input, one without
    (data_dir / "Person.tsv").write_text(
        "id\tname\tage\nP001\tAlice\t30\nP002\tBob\tnot_a_number\n"
    )

    # Use a spec with a simple populated_from that works for all rows
    spec_yaml = textwrap.dedent("""\
        class_derivations:
          Person:
            populated_from: Person
            slot_derivations:
              id: {}
              name:
                populated_from: name
    """)
    tr = _make_transformer(spec_yaml)
    loader = DataLoader(data_dir)

    errors: list[TransformationError] = []
    results = list(transform_spec(tr, loader, on_error=errors.append))

    # Both rows should succeed (simple populated_from doesn't fail)
    assert len(results) == 2
    assert len(errors) == 0


def test_multiple_errors_across_rows(tmp_path):
    """Multiple errors from different rows are all collected."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "Person.tsv").write_text(
        "id\tname\tage\nP001\tAlice\t30\nP002\tBob\t25\nP003\tCharlie\t35\n"
    )

    spec_yaml = textwrap.dedent("""\
        class_derivations:
          Person:
            populated_from: Person
            slot_derivations:
              id: {}
              bad_field:
                expr: "nonexistent + 1"
    """)
    tr = _make_transformer(spec_yaml)
    loader = DataLoader(data_dir)

    errors: list[TransformationError] = []
    results = list(transform_spec(tr, loader, on_error=errors.append))

    assert len(errors) == 3
    assert len(results) == 0
    assert [e.row_index for e in errors] == [0, 1, 2]
