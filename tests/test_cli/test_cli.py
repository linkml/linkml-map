import unittest

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


class TestCommandLineInterface(unittest.TestCase):
    """
    Tests all command-line subcommands
    """

    def setUp(self) -> None:
        runner = CliRunner(mix_stderr=False)
        self.runner = runner

    def test_main_help(self):
        result = self.runner.invoke(main, ["--help"])
        out = result.stdout
        self.assertIn("derive-schema", out)
        self.assertIn("map-data", out)
        self.assertEqual(0, result.exit_code)

    def test_derive_schema(self):
        cmd = ["derive-schema", "-T", str(PERSONINFO_TR), str(PERSONINFO_SRC_SCHEMA)]
        result = self.runner.invoke(main, cmd)
        self.assertEqual(0, result.exit_code)
        out = result.stdout
        # schema = yaml_loader.loads(str(out), SchemaDefinition)
        # expected = yaml_loader.load(str(PERSONINFO_TGT_SCHEMA), SchemaDefinition)
        # self.ensure_schemas_equivalent(schema, expected)
        sv = SchemaView(out)
        self.assertIn("Agent", sv.all_classes().keys())
        # self.assertIn("NamedThing", sv.all_classes().keys())

    def test_map_data(self):
        cmd = [
            "map-data",
            "--unrestricted-eval",
            "-T",
            str(PERSONINFO_TR),
            "-s",
            str(PERSONINFO_SRC_SCHEMA),
            str(PERSONINFO_CONTAINER_DATA),
        ]
        result = self.runner.invoke(main, cmd)
        self.assertEqual(0, result.exit_code)
        out = result.stdout
        tr_data = yaml.safe_load(out)
        self.assertEqual("fred bloggs", tr_data["agents"][0]["label"])

    def test_map_data2(self):
        cmd = [
            "map-data",
            "-T",
            str(DENORM_SPECIFICATION),
            "-s",
            str(NORM_SCHEMA),
            str(FLATTENING_DATA),
        ]
        result = self.runner.invoke(main, cmd)
        self.assertEqual(0, result.exit_code)
        out = result.stdout
        tr_data = yaml.safe_load(out)
        m = tr_data["mappings"][0]
        self.assertEqual(m["subject_id"], "X:1")
        self.assertEqual(m["subject_name"], "x1")

    def ensure_schemas_equivalent(self, s1: SchemaDefinition, s2: SchemaDefinition):
        self.assertCountEqual(s1.classes, s2.classes)
        self.assertCountEqual(s1.slots, s2.slots)
