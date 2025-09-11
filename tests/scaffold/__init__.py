import copy
from linkml_runtime import SchemaView
from pathlib import Path
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

LOADED_DATA = {
    "source_schema": SchemaView(SOURCE_SCHEMA),
    "target_schema": SchemaView(TARGET_SCHEMA),
    "transform_spec": yaml_load(TRANSFORM_SPEC),
    "input_data": yaml_load(INPUT_DATA),
    "expected": yaml_load(EXPECTED_DATA),
}

def new_scaffold():
    return copy.deepcopy(LOADED_DATA)
