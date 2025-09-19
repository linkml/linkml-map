from pathlib import Path

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
