"""Shared CLI test fixtures."""

import click
import pytest
from click.testing import CliRunner


def _make_runner() -> CliRunner:
    """Create a CliRunner with version-aware mix_stderr support.

    click 8.3+ removed the ``mix_stderr`` kwarg (its prior behavior
    of *not* mixing is now the unconditional default), so we only
    pass it for older versions to maintain backward compatibility.
    """
    major, minor = click.__version__.split(".")[:2]
    if int(major) >= 8 and int(minor) >= 3:
        return CliRunner()
    return CliRunner(mix_stderr=False)


@pytest.fixture
def runner() -> CliRunner:
    """Provide a CliRunner that works across click versions."""
    return _make_runner()