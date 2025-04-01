"""Tests all command-line subcommands."""

import pytest

import yaml
from click.testing import CliRunner
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SchemaDefinition

from linkml_map.cli.cli import main
from tests import (
    DENORM_SPECIFICATION,
    FLATTENING_DATA,
    NORM_SCHEMA,
    PERSONINFO_CONTAINER_DATA,
    PERSONINFO_SRC_SCHEMA,
    PERSONINFO_TR,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def test_main_help(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--help"])
    out = result.stdout
    assert "derive-schema" in out
    assert "map-data" in out
    assert result.exit_code == 0


def test_derive_schema(runner: CliRunner) -> None:
    cmd = ["derive-schema", "-T", str(PERSONINFO_TR), str(PERSONINFO_SRC_SCHEMA)]
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    out = result.stdout
    # schema = yaml_loader.loads(str(out), SchemaDefinition)
    # expected = yaml_loader.load(str(PERSONINFO_TGT_SCHEMA), SchemaDefinition)
    # self.ensure_schemas_equivalent(schema, expected)
    sv = SchemaView(out)
    assert "Agent" in sv.all_classes().keys()
    # self.assertIn("NamedThing", sv.all_classes().keys())


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
    assert "fred bloggs" == tr_data["agents"][0]["label"]


def test_map_data2(runner: CliRunner) -> None:
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


def ensure_schemas_equivalent(s1: SchemaDefinition, s2: SchemaDefinition):
    assert len(s1.classes) == len(s2.classes)
    assert len(s1.slots) == len(s2.slots)
