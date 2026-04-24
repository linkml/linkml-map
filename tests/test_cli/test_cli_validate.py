"""Tests for the validate-spec CLI command."""

import pytest
from click.testing import CliRunner

from linkml_map.cli.cli import main
from tests import (
    FLATTENING_SRC_SCHEMA,
    FLATTENING_TGT_SCHEMA,
    FLATTENING_TR,
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TR,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def test_validate_spec_valid_file(runner: CliRunner) -> None:
    """A valid trans-spec file exits 0 and prints ok."""
    result = runner.invoke(main, ["validate-spec", str(FLATTENING_TR)])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_validate_spec_multiple_files(runner: CliRunner) -> None:
    """Multiple valid files all report ok."""
    result = runner.invoke(main, ["validate-spec", str(FLATTENING_TR), str(PERSONINFO_TR)])
    assert result.exit_code == 0
    assert result.output.count("ok") == 2


def test_validate_spec_invalid_file(runner: CliRunner, tmp_path) -> None:
    """An invalid spec exits 1 and prints errors to stderr."""
    bad = tmp_path / "bad.transform.yaml"
    bad.write_text("not_a_real_field: oops\n")
    result = runner.invoke(main, ["validate-spec", str(bad)])
    assert result.exit_code == 1
    assert "not_a_real_field" in result.stderr


def test_validate_spec_non_mapping(runner: CliRunner, tmp_path) -> None:
    """A YAML list (not a mapping) exits 1."""
    bad = tmp_path / "list.yaml"
    bad.write_text("- item\n")
    result = runner.invoke(main, ["validate-spec", str(bad)])
    assert result.exit_code == 1
    assert "mapping" in result.stderr.lower()


def test_validate_spec_mixed_valid_invalid(runner: CliRunner, tmp_path) -> None:
    """With mixed files, valid ones report ok, invalid ones report errors, exits 1."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("bogus_field: 123\n")
    result = runner.invoke(main, ["validate-spec", str(FLATTENING_TR), str(bad)])
    assert result.exit_code == 1
    assert "ok" in result.output
    assert "bogus_field" in result.stderr


def test_validate_spec_appears_in_help(runner: CliRunner) -> None:
    """The validate-spec command appears in the main help."""
    result = runner.invoke(main, ["--help"])
    assert "validate-spec" in result.output


# ---------------------------------------------------------------------------
# Semantic validation CLI tests
# ---------------------------------------------------------------------------


def test_validate_spec_with_schemas(runner: CliRunner) -> None:
    """Validation with source and target schemas exits 0 for a valid spec."""
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--source-schema",
            str(FLATTENING_SRC_SCHEMA),
            "--target-schema",
            str(FLATTENING_TGT_SCHEMA),
            str(FLATTENING_TR),
        ],
    )
    assert result.exit_code == 0, f"stderr: {result.stderr}"
    assert "ok" in result.output


def test_validate_spec_semantic_errors(runner: CliRunner, tmp_path) -> None:
    """A spec referencing a nonexistent target class errors with --target-schema."""
    spec = tmp_path / "bad_ref.yaml"
    spec.write_text("class_derivations:\n  NonExistentClass:\n    populated_from: Person\n")
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--target-schema",
            str(PERSONINFO_SRC_SCHEMA),
            str(spec),
        ],
    )
    assert result.exit_code == 1
    assert "NonExistentClass" in result.stderr


def test_validate_spec_strict_flag(runner: CliRunner, tmp_path) -> None:
    """With --strict, expression warnings become errors."""
    spec = tmp_path / "expr_warn.yaml"
    spec.write_text(
        "class_derivations:\n"
        "  Person:\n"
        "    populated_from: Person\n"
        "    slot_derivations:\n"
        "      primary_email:\n"
        '        expr: "bogus_slot"\n'
    )
    # Without strict: exit 0 (warning only)
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--source-schema",
            str(PERSONINFO_SRC_SCHEMA),
            str(spec),
        ],
    )
    assert result.exit_code == 0

    # With strict: exit 1 (warning promoted to error)
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--source-schema",
            str(PERSONINFO_SRC_SCHEMA),
            "--strict",
            str(spec),
        ],
    )
    assert result.exit_code == 1
    assert "bogus_slot" in result.stderr


def test_validate_spec_no_warnings(runner: CliRunner, tmp_path) -> None:
    """With --no-warnings, warnings are suppressed from stderr."""
    spec = tmp_path / "expr_warn.yaml"
    spec.write_text(
        "class_derivations:\n"
        "  Person:\n"
        "    populated_from: Person\n"
        "    slot_derivations:\n"
        "      primary_email:\n"
        '        expr: "bogus_slot"\n'
    )
    # Without --no-warnings: warnings appear in stderr
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--source-schema",
            str(PERSONINFO_SRC_SCHEMA),
            str(spec),
        ],
    )
    assert "bogus_slot" in result.stderr

    # With --no-warnings: warnings suppressed
    result = runner.invoke(
        main,
        [
            "validate-spec",
            "--source-schema",
            str(PERSONINFO_SRC_SCHEMA),
            "--no-warnings",
            str(spec),
        ],
    )
    assert "bogus_slot" not in result.stderr
    assert result.exit_code == 0
