"""Collect the compliance suite's markdown output and write it to a file.

The suite narrates itself as it runs: each feature set and combination emits the
schema, specification, and objects it exercised. Those fragments are buffered here
and assembled into a single document at the end of the session.

The report is only written when ``--compliance-out`` is given, so an ordinary test
run never touches the working tree, and a filtered run (``-k``) cannot truncate the
document to whatever subset happened to execute.
"""

import re
from datetime import date
from pathlib import Path

HEADER = """# LinkML-Map Compliance Suite

This is the output from running the full compliance test suite.

```yaml
Time_executed: {generated_on}
Package: {package}
```

It is organized into **Feature Sets** that test a particular feature or group of features,
and **combinations** of different schemas, input objects, and transformation specifications.
This is intended to exhaustively test all combinations of features, and provide informative
output.

Each test is designed to demonstrate:

- data mapping (transformation)
- derived schemas
- inversion (reverse transformation) (in some cases)
- compilation to other frameworks (coming soon)

"""

# The one line that legitimately differs between two runs of identical content.
TIMESTAMP = re.compile(r"^Time_executed: .*$", re.MULTILINE)

_fragments: list[str] = []


def emit(text: str = "") -> None:
    """Add a fragment to the report."""
    _fragments.append(text)


def normalize(document: str) -> str:
    """Return ``document`` in the shape the pre-commit hooks would leave it in.

    trailing-whitespace and end-of-file-fixer run over this file, so emitting
    anything they would rewrite puts the generator and the hooks in a loop that
    the drift check can never settle.
    """
    return "\n".join(line.rstrip() for line in document.split("\n")).rstrip("\n") + "\n"


def render(package: str, generated_on: str) -> str:
    """Return the assembled markdown document."""
    body = "\n".join(_fragments)
    return normalize(HEADER.format(generated_on=generated_on, package=package) + body)


def write_if_changed(path: Path, document: str) -> bool:
    """Write ``document`` to ``path`` unless only its timestamp would move.

    Returns True if the file was written. Rewriting on every run would restamp the
    date and defeat the CI drift check, so the timestamp advances only when the
    substance of the report does.
    """
    if path.exists() and TIMESTAMP.sub("", path.read_text()) == TIMESTAMP.sub("", document):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document)
    return True


def write(path: Path, package: str) -> bool:
    """Write the accumulated report to ``path``, stamped with today's date."""
    return write_if_changed(path, render(package, date.today().strftime("%Y-%m-%d")))
