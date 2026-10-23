"""The spec operations exported from ``linkml_map``: each matches its CLI command."""

import pytest
import yaml
from click.testing import CliRunner
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper

from linkml_map import derive_schema, graphviz, invert, load_specification
from linkml_map.cli.cli import main
from linkml_map.inference.inverter import NonInvertibleSpecificationError
from tests import PERSONINFO_SRC_SCHEMA, PERSONINFO_TR


def _cli_yaml(*args: str) -> dict:
    result = CliRunner().invoke(main, [*args, "-T", str(PERSONINFO_TR), str(PERSONINFO_SRC_SCHEMA)])
    assert result.exit_code == 0, result.output
    return yaml.safe_load(result.stdout)


@pytest.mark.parametrize(
    ("spec", "schema"),
    [
        (str(PERSONINFO_TR), str(PERSONINFO_SRC_SCHEMA)),
        (PERSONINFO_TR, PERSONINFO_SRC_SCHEMA),
        (yaml.safe_load(PERSONINFO_TR.read_text()), SchemaView(str(PERSONINFO_SRC_SCHEMA))),
        (load_specification(PERSONINFO_TR), SchemaView(str(PERSONINFO_SRC_SCHEMA)).schema),
    ],
    ids=["str", "path", "dict-schemaview", "spec-schemadefinition"],
)
def test_derive_schema_matches_cli(spec, schema):
    """``derive_schema`` gives the same target schema as ``linkml-map derive-schema``, whatever the input form."""
    assert yaml.safe_load(yaml_dumper.dumps(derive_schema(spec, schema))) == _cli_yaml("derive-schema")


def test_invert_matches_cli():
    """``invert`` gives the same inverse specification as ``linkml-map invert``."""
    inverted = invert(PERSONINFO_TR, PERSONINFO_SRC_SCHEMA, strict=False)
    assert yaml.safe_load(yaml_dumper.dumps(inverted)) == _cli_yaml("invert", "--no-strict")


def test_invert_strict_raises_on_non_invertible_expression():
    """Personinfo derives ``age`` with an expression, which strict inversion refuses."""
    with pytest.raises(NonInvertibleSpecificationError, match="age"):
        invert(PERSONINFO_TR, PERSONINFO_SRC_SCHEMA)


def test_graphviz_draws_mapped_classes():
    """``graphviz`` draws the source and target classes of each class derivation."""
    source = graphviz(PERSONINFO_TR, PERSONINFO_SRC_SCHEMA).source
    assert "Person" in source
    assert "Agent" in source


def test_load_specification_accepts_path_objects():
    """A ``Path`` loads like a ``str`` path."""
    assert load_specification(PERSONINFO_TR) == load_specification(str(PERSONINFO_TR))
