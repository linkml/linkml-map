"""Tests for the validate-spec CLI command."""

import pytest
from click.testing import CliRunner

from linkml_map.cli.cli import main
from tests import FLATTENING_TR, PERSONINFO_TR

EXAMPLE_DIR = PERSONINFO_TR.parent.parent.parent


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
