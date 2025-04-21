"""Tests all command-line subcommands."""

from collections.abc import Generator
from pathlib import Path
import re
from typing import Any, Optional, Union

import pytest
import yaml
from click.testing import CliRunner, Result
from linkml_runtime import SchemaView

from linkml_map.cli.cli import dump_output, main
from tests import (
    DENORM_SPECIFICATION,
    FLATTENING_DATA,
    NORM_SCHEMA,
    PERSONINFO_CONTAINER_DATA,
    PERSONINFO_DERIVED,
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TR,
    PERSONINFO_TR_COMPILED_MD,
    PERSONINFO_TR_COMPILED_PY,
)

DERIVED_SCHEMA_NAME_LINE = "name: personinfo-derived"


@pytest.fixture
def runner() -> CliRunner:
    """
    Command line interface test runner.

    :return: command line interface runner
    :rtype: CliRunner
    """
    return CliRunner(mix_stderr=False)


def test_main_help(runner: CliRunner) -> None:
    """
    Ensure that the help command contains the appropriate text.

    :param runner: command line interface runner
    :type runner: CliRunner
    """
    result = runner.invoke(main, ["--help"])
    out = result.stdout
    assert "derive-schema" in out
    assert "map-data" in out
    assert result.exit_code == 0


def check_result(result: Result, expected_file: Path, output_param: Optional[str] = None) -> None:
    """
    Check that the result of running a function matches the expected output.

    :param result: result object from the CliRunner
    :type result: Result
    :param expected_file: path to the expected result
    :type expected_file: Path
    :param output_param: output param supplied to the function, defaults to None
    :type output_param: Optional[str], optional
    """
    if output_param:
        with output_param.open() as fh:
            function_output = fh.read()
    else:
        function_output = result.stdout

    with expected_file.open() as fh:
        assert fh.read() == function_output


@pytest.mark.parametrize("output", [None, "output.py"])
@pytest.mark.parametrize("target", [None, "python", "markdown", "klingon"])
def test_compile(
    runner: CliRunner,
    target: Optional[str],
    output: Optional[str],
    tmp_path: Generator[Path, None, None],
) -> None:
    """
    Basic test of the python compiler functionality.

    :param runner: command line interface runner
    :type runner: CliRunner
    :param target: target language for compiled transformer
    :type target: Optional[str]
    :param output: output file, optional
    :type output: Optional[str]
    :param tmp_path: tmp dir for writing output to (if appropriate)
    :type tmp_path: Generator[Path, None, None]
    """
    cmd = [
        "compile",
        "-T",
        str(PERSONINFO_TR),
        "-s",
        str(PERSONINFO_SRC_SCHEMA),
    ]
    if target:
        cmd.extend(["--target", target])
    if output:
        output = tmp_path / output
        cmd.extend(["--output", str(output)])

    result = runner.invoke(main, cmd)
    if target and target == "klingon":
        assert result.exit_code != 0
        assert isinstance(result.exception, NotImplementedError)
        assert result.exception.args[0] == "Compiler klingon not implemented"
        return

    assert result.exit_code == 0
    if target and target == "markdown":
        check_result(result, PERSONINFO_TR_COMPILED_MD, output)
    else:
        check_result(result, PERSONINFO_TR_COMPILED_PY, output)


@pytest.mark.parametrize("output", [None, "output.yaml"])
def test_derive_schema(
    runner: CliRunner, output: Optional[str], tmp_path: Generator[Path, None, None]
) -> None:
    """
    Test schema derivation.

    :param runner: command line interface runner
    :type runner: CliRunner
    :param output: output file, optional
    :type output: Optional[str]
    :param tmp_path: tmp dir for writing output to (if appropriate)
    :type tmp_path: Generator[Path, None, None]
    """
    cmd = ["derive-schema", "-T", str(PERSONINFO_TR), str(PERSONINFO_SRC_SCHEMA)]
    if output:
        output = tmp_path / output
        cmd.extend(["--output", str(output)])
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    check_result(result, PERSONINFO_DERIVED, output)
    result_schema = result.stdout
    if output:
        with output.open() as fh:
            result_schema = fh.read()
    assert DERIVED_SCHEMA_NAME_LINE in result_schema
    sv = SchemaView(result_schema)
    assert "Agent" in sv.all_classes()


def test_map_data(runner: CliRunner) -> None:
    cmd = [
        "map-data",
        "--unrestricted-eval",
        "-T",
        str(PERSONINFO_TR),
        "-s",
        str(PERSONINFO_SRC_SCHEMA),
        str(PERSONINFO_CONTAINER_DATA),
    ]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    out = result.stdout
    tr_data = yaml.safe_load(out)
    assert tr_data["agents"][0]["label"] == "fred bloggs"


def test_map_data_norm_denorm(runner: CliRunner) -> None:
    cmd = [
        "map-data",
        "-T",
        str(DENORM_SPECIFICATION),
        "-s",
        str(NORM_SCHEMA),
        str(FLATTENING_DATA),
    ]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    out = result.stdout
    tr_data = yaml.safe_load(out)
    m = tr_data["mappings"][0]
    assert m["subject_id"] == "X:1"
    assert m["subject_name"] == "x1"


EXPECTED_OUTPUT = {
    "dict": {"input": {"that": "this"}, "yaml": "that: this\n"},
    "list": {
        "input": ["this", "that", "the other"],
        "yaml": "- this\n- that\n- the other\n",
    },
    "string": {
        "input": "But how long is it?",
        "yaml": "But how long is it?\n...\n",  # eh??
        None: "But how long is it?",
    },
}


@pytest.mark.parametrize("file_path", [None, "output.txt"])
@pytest.mark.parametrize("output_format", [None, "yaml"])
@pytest.mark.parametrize("output_data", EXPECTED_OUTPUT.keys())
def test_dump_output(
    capsys: Generator[pytest.CaptureFixture, None, None],
    tmp_path: Generator[Path, None, None],
    file_path: Optional[str],
    output_format: Optional[str],
    output_data: Union[dict, list],
) -> None:
    """Ensure that the dump_output function does what it says."""
    if file_path:
        file_path = str(tmp_path / file_path)

    # if there is no `output_format` key, this data cannot be dumped
    if output_format not in EXPECTED_OUTPUT[output_data]:
        with pytest.raises(
            TypeError, match=re.escape(f"write() argument must be str, not {output_data}")
        ):
            dump_output(EXPECTED_OUTPUT[output_data]["input"], output_format, file_path)
        return

    dump_output(EXPECTED_OUTPUT[output_data]["input"], output_format, file_path)
    expected_text = EXPECTED_OUTPUT[output_data][output_format]
    if not file_path:
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == expected_text
        return

    with Path(file_path).open() as f:
        assert f.read() == expected_text


@pytest.mark.parametrize(
    ("param", "value", "error", "message"),
    [
        ("output_format", "json", NotImplementedError, "Output format json is not supported"),
        ("output_data", None, ValueError, "No output to be printed"),
        ("file_path", "path/to/a/dir", FileNotFoundError, "No such file or directory"),
    ],
)
def test_dump_output_fail(param: str, value: Optional[str], error: Exception, message: str) -> None:
    """
    Ensure that invalid input causes dump_output to fail.
    """
    default_params = {"output_data": {"this": "that"}, "output_format": "yaml", "file_path": None}
    test_params = {**default_params, param: value}
    with pytest.raises(error, match=message):
        dump_output(**test_params)
