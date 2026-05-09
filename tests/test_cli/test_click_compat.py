"""Verify CliRunner calls are forward-compatible with click 8.3+."""

import ast
from pathlib import Path

import pytest


def test_cli_runner_no_mix_stderr():
    """No CliRunner call should pass mix_stderr keyword.

    The ``mix_stderr`` parameter was removed in click 8.3+.
    See https://github.com/linkml/linkml-map/issues/218.
    """
    test_dir = Path(__file__).parent
    for py_file in test_dir.glob("*.py"):
        if py_file.name == Path(__file__).name:
            continue
        source = py_file.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "mix_stderr":
                pytest.fail(f"{py_file.name} uses removed 'mix_stderr' kwarg")
