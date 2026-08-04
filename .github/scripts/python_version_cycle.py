"""Report Python versions the CI matrix should pick up or drop.

Compares the ``python-version`` matrix in ``.github/workflows/main.yaml`` against
upstream release data from endoflife.date. Prints a Markdown report to stdout when
there is something to act on, and prints nothing otherwise.
"""

import datetime as dt
import json
import re
import urllib.request
from pathlib import Path

ENDOFLIFE_URL = "https://endoflife.date/api/python.json"
MATRIX_PATTERN = re.compile(r"python-version:\s*\[([^\]]*)\]")
QUOTED_VERSION = re.compile(r"['\"]([0-9]+\.[0-9]+)['\"]")
REQUIRES_PYTHON = re.compile(r"^requires-python\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "main.yaml"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def version_key(cycle: str) -> tuple[int, ...]:
    """Return a sortable key for a ``major.minor`` version string."""
    return tuple(int(part) for part in cycle.split("."))


def matrix_versions(workflow: Path) -> list[str]:
    """Return the Python versions listed in the workflow's test matrix."""
    match = MATRIX_PATTERN.search(workflow.read_text())
    if match is None:
        msg = f"No 'python-version: [...]' matrix found in {workflow}"
        raise ValueError(msg)
    versions = QUOTED_VERSION.findall(match.group(1))
    if not versions:
        msg = f"No quoted versions in the 'python-version' matrix in {workflow}"
        raise ValueError(msg)
    return versions


def requires_python(pyproject: Path) -> str:
    """Return the ``requires-python`` specifier declared in pyproject.toml.

    Read with a regex rather than ``tomllib`` so this stays importable on Python 3.10,
    which the test suite still runs against.
    """
    match = REQUIRES_PYTHON.search(pyproject.read_text())
    if match is None:
        msg = f"No 'requires-python' declaration found in {pyproject}"
        raise ValueError(msg)
    return match.group(1)


def fetch_cycles(url: str = ENDOFLIFE_URL) -> dict[str, dt.date]:
    """Return a mapping of Python ``major.minor`` cycle to its end-of-life date."""
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    return {
        entry["cycle"]: dt.date.fromisoformat(entry["eol"]) for entry in payload if isinstance(entry.get("eol"), str)
    }


def build_report(versions: list[str], eol_dates: dict[str, dt.date], today: dt.date, specifier: str) -> str:
    """Return a Markdown report of versions to drop and add, or an empty string."""
    expired = [v for v in versions if v in eol_dates and eol_dates[v] <= today]
    newest_tested = max(versions, key=version_key)
    untested = [
        cycle for cycle, eol in eol_dates.items() if eol > today and version_key(cycle) > version_key(newest_tested)
    ]

    if not expired and not untested:
        return ""

    lines = [
        "The Python support window has moved since this repo was last updated.",
        "",
        f"- CI matrix: {', '.join(versions)}",
        f"- `requires-python`: `{specifier}`",
        "",
    ]
    if expired:
        lines.append("### Reached end of life")
        lines.append("")
        lines += [f"- **{v}** — EOL {eol_dates[v].isoformat()}" for v in sorted(expired, key=version_key)]
        lines.append("")
        lines.append(
            "Dropping a version raises the `requires-python` floor, which is a breaking "
            "change for downstream consumers — check what `linkml` and `linkml-runtime` "
            "currently require before acting."
        )
        lines.append("")
    if untested:
        lines.append("### Released but not in the matrix")
        lines.append("")
        lines += [f"- **{v}** — supported until {eol_dates[v].isoformat()}" for v in sorted(untested, key=version_key)]
        lines.append("")
    lines.append("_Opened automatically by the `python-version-cycle` workflow._")
    return "\n".join(lines)


def main() -> None:
    """Print the report, if any, to stdout."""
    versions = matrix_versions(WORKFLOW)
    report = build_report(versions, fetch_cycles(), dt.date.today(), requires_python(PYPROJECT))
    if report:
        print(report)


if __name__ == "__main__":
    main()
