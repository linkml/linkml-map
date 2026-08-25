"""Tests for the compliance report writer.

The timestamp rule is what lets the doc carry a generation date and still be
drift-checked in CI, so it is the part worth pinning down.
"""

from pathlib import Path

import pytest

from tests.test_compliance.report import normalize, write_if_changed

DOC = "```yaml\nTime_executed: 2026-08-06\n```\n\n## Feature Set: test_join\n"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("**Source Schema**: \n\nbody", "**Source Schema**:\n\nbody\n"),
        ("body\n\n\n", "body\n"),
        ("trailing tabs\t\nbody", "trailing tabs\nbody\n"),
        ("already clean\n", "already clean\n"),
    ],
)
def test_normalize_matches_what_the_hooks_would_do(raw: str, expected: str) -> None:
    """The generator must emit what trailing-whitespace and end-of-file-fixer accept.

    Otherwise the hooks rewrite the file, the next regeneration undoes them, and the
    drift check never settles.
    """
    assert normalize(raw) == expected


def test_writes_when_the_file_is_absent(tmp_path: Path) -> None:
    """A missing report is created, parent directories included."""
    target = tmp_path / "specification" / "compliance.md"
    assert write_if_changed(target, DOC) is True
    assert target.read_text() == DOC


@pytest.mark.parametrize("existing", [None, DOC.replace("\n", "\r\n")], ids=["absent", "crlf"])
def test_writes_lf_line_endings(tmp_path: Path, existing: str | None) -> None:
    """The bytes on disk are what ``normalize`` produced, on every platform.

    A CRLF report is what a Windows run used to leave behind. Comparing it as text
    would call it unchanged and strand it, so it has to count as a difference: the
    pre-commit hooks rewrite CRLF, and the drift check can never settle while they do.
    """
    target = tmp_path / "compliance.md"
    if existing is not None:
        target.write_bytes(existing.encode("utf-8"))
    write_if_changed(target, DOC)
    assert target.read_bytes() == DOC.encode("utf-8")


@pytest.mark.parametrize(
    ("stamp", "expected_write"),
    [
        ("Time_executed: 2026-08-06", False),
        ("Time_executed: 2001-01-01", False),
    ],
)
def test_timestamp_alone_does_not_trigger_a_write(tmp_path: Path, stamp: str, expected_write: bool) -> None:
    """Identical content leaves the file untouched however stale its date."""
    target = tmp_path / "compliance.md"
    target.write_text(DOC.replace("Time_executed: 2026-08-06", stamp))
    before = target.read_text()
    assert write_if_changed(target, DOC) is expected_write
    assert target.read_text() == before, "an unchanged report must not be restamped"


def test_changed_content_rewrites_and_carries_the_new_stamp(tmp_path: Path) -> None:
    """A real change is written out, taking the fresh timestamp with it."""
    target = tmp_path / "compliance.md"
    target.write_text(DOC.replace("Time_executed: 2026-08-06", "Time_executed: 2001-01-01"))
    changed = DOC.replace("test_join", "test_join_rewritten")
    assert write_if_changed(target, changed) is True
    assert target.read_text() == changed
    assert "2026-08-06" in target.read_text()
