import copy
from importlib.resources import files
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

FILE_PATHS = {
    "source_schema": SOURCE_SCHEMA,
    "target_schema": TARGET_SCHEMA,
    "transform_spec": TRANSFORM_SPEC,
    "input_data": INPUT_DATA,
    "expected": EXPECTED_DATA,
}

LOADED_DATA = {k: yaml.safe_load(p.read_text()) for k, p in FILE_PATHS.items()}

def make_scaffold():
    """Return a fresh deep copy for each test."""
    return copy.deepcopy(LOADED_DATA)
