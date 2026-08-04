"""Tests for the Python support-window check driven by the `python-version-cycle` workflow."""

import datetime as dt
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "python_version_cycle.py"

EOL_DATES = {
    "3.9": dt.date(2025, 10, 31),
    "3.10": dt.date(2026, 10, 31),
    "3.11": dt.date(2027, 10, 31),
    "3.12": dt.date(2028, 10, 31),
    "3.13": dt.date(2029, 10, 31),
    "3.14": dt.date(2030, 10, 31),
}


def _load_script():
    """Load the workflow helper, which lives outside the importable package."""
    spec = importlib.util.spec_from_file_location("python_version_cycle", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cycle = _load_script()


@pytest.mark.parametrize(
    ("versions", "expected"),
    [
        (["3.9", "3.10"], ["3.9", "3.10"]),
        (["3.10", "3.9"], ["3.9", "3.10"]),
        (["3.13", "3.9", "3.10"], ["3.9", "3.10", "3.13"]),
    ],
)
def test_version_key_orders_numerically_not_lexically(versions: list[str], expected: list[str]) -> None:
    """'3.9' must sort below '3.10', which plain string comparison gets backwards."""
    assert sorted(versions, key=cycle.version_key) == expected


def test_no_report_when_the_matrix_is_current() -> None:
    """A matrix covering every live version with nothing newer produces no report."""
    report = cycle.build_report(["3.11", "3.12", "3.13", "3.14"], EOL_DATES, dt.date(2026, 11, 1), ">=3.11")
    assert report == ""


def test_expired_version_is_reported_for_dropping() -> None:
    """A matrix entry past its EOL date is called out, with the downstream caveat."""
    report = cycle.build_report(["3.10", "3.11", "3.14"], EOL_DATES, dt.date(2026, 11, 1), ">=3.10")
    assert "Reached end of life" in report
    assert "**3.10** — EOL 2026-10-31" in report
    assert "breaking change for downstream consumers" in report
    assert "Released but not in the matrix" not in report


def test_released_version_missing_from_matrix_is_reported() -> None:
    """A supported release newer than everything tested is called out for adding."""
    report = cycle.build_report(["3.10", "3.11", "3.12", "3.13"], EOL_DATES, dt.date(2026, 8, 3), ">=3.10")
    assert "Released but not in the matrix" in report
    assert "**3.14** — supported until 2030-10-31" in report
    assert "Reached end of life" not in report


def test_expired_and_missing_are_reported_together() -> None:
    """Both sections appear when a version has expired and a newer one is untested."""
    report = cycle.build_report(["3.10", "3.11"], EOL_DATES, dt.date(2026, 11, 1), ">=3.10")
    assert "Reached end of life" in report
    assert "Released but not in the matrix" in report


def test_version_absent_from_upstream_data_is_not_flagged_as_expired() -> None:
    """A matrix entry with no upstream EOL record (e.g. a prerelease) is left alone."""
    report = cycle.build_report(["3.14", "3.15"], EOL_DATES, dt.date(2026, 11, 1), ">=3.14")
    assert report == ""


def test_matrix_versions_parses_the_real_workflow() -> None:
    """The parser reads the matrix out of the workflow this repo actually ships."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yaml"
    versions = cycle.matrix_versions(workflow)
    assert versions
    assert all(v.startswith("3.") for v in versions)


@pytest.mark.parametrize(
    "matrix",
    [
        "        python-version: [3.10, 3.11]\n",
        "        python-version: []\n",
    ],
)
def test_unquoted_matrix_entries_raise_rather_than_parsing_to_nothing(tmp_path: Path, matrix: str) -> None:
    """A matrix the version regex can't read fails at the parse, not later on an empty list."""
    workflow = tmp_path / "main.yaml"
    workflow.write_text(f"jobs:\n  test:\n    strategy:\n      matrix:\n{matrix}")
    with pytest.raises(ValueError, match="No quoted versions"):
        cycle.matrix_versions(workflow)


def test_requires_python_reads_pyproject() -> None:
    """The pyproject reader returns the declared specifier."""
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    assert cycle.requires_python(pyproject).startswith(">=3.")
