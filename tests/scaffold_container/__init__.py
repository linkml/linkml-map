from pathlib import Path

SOURCE = "source"
TARGET = "target"
TRANSFORM = "transform"
DATA = "data"
EXPECTED = "expected"

SCAFFOLD_DIR = Path(__file__).parent.resolve()

SOURCE_SCHEMA = SCAFFOLD_DIR / SOURCE / "container.yaml"
TARGET_SCHEMA = SCAFFOLD_DIR / TARGET / "flat_person.yaml"
TRANSFORM_SPEC = SCAFFOLD_DIR / TRANSFORM / "flatten_fk.transform.yaml"

INPUT_DATA = SCAFFOLD_DIR / DATA / "Container-001.yaml"
EXPECTED_DATA = SCAFFOLD_DIR / EXPECTED / "Container-001.transformed.yaml"
