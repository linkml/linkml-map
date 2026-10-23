"""``load_specification`` accepts a spec in any form and gives the same specification."""

import pytest
import yaml

from linkml_map import load_specification
from tests import PERSONINFO_TR


@pytest.mark.parametrize(
    "spec",
    [str(PERSONINFO_TR), PERSONINFO_TR, yaml.safe_load(PERSONINFO_TR.read_text())],
    ids=["str", "path", "dict"],
)
def test_load_specification_input_forms(spec):
    """A str path, a Path and the file's parsed contents load to the same specification."""
    assert load_specification(spec) == load_specification(str(PERSONINFO_TR))


def test_load_specification_normalizes_dict():
    """A dict is normalized like a file's contents, so dict-keyed class derivations become a named list."""
    spec = load_specification({"class_derivations": {"Agent": {"populated_from": "Person"}}})
    assert [cd.name for cd in spec.class_derivations] == ["Agent"]
