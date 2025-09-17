import copy
from linkml_runtime import SchemaView
from pathlib import Path
from types import MappingProxyType
import yaml

SOURCE = "source"
TARGET = "target"
TRANSFORM = "transform"
DATA = "data"
EXPECTED = "expected"

SCAFFOLD_DIR = Path(__file__).parent.resolve()

SOURCE_SCHEMA = SCAFFOLD_DIR / SOURCE / "person.yaml"
TARGET_SCHEMA = SCAFFOLD_DIR / TARGET / "agent.yaml"
TRANSFORM_SPEC = SCAFFOLD_DIR / TRANSFORM / "person_to_agent.transform.yaml"

INPUT_DATA = SCAFFOLD_DIR / DATA / "Person-001.yaml"
EXPECTED_DATA = SCAFFOLD_DIR / EXPECTED / "Person-001.transformed.yaml"

def yaml_load(file_path: Path) -> dict:
    return yaml.safe_load(file_path.read_text())

class StrictDict(dict):
    """A dict that disallows overwriting with a different value."""

    def __setitem__(self, key, value):
        if key in self and self[key] != value:
            raise ValueError(
                f"Duplicate assignment to expected key '{key}': "
                f"existing={self[key]!r}, new={value!r}"
            )
        super().__setitem__(key, value)

# Load statically  -- Do not mutate directly
_LOADED_DATA = MappingProxyType({
    "source_schema": SchemaView(SOURCE_SCHEMA),
    "target_schema": SchemaView(TARGET_SCHEMA),
    "transform_spec": yaml_load(TRANSFORM_SPEC),
    "input_data": yaml_load(INPUT_DATA),
    "expected": StrictDict(yaml_load(EXPECTED_DATA)),
})

def new_scaffold():
    return copy.deepcopy(dict(_LOADED_DATA))
