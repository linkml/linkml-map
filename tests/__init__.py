import os
from pathlib import Path

ROOT = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = Path(ROOT) / "input"
OUTPUT_DIR = Path(ROOT) / "output"
SCHEMA1 = str(INPUT_DIR / 'personinfo_s1.yaml')
SCHEMA2 = str(INPUT_DIR / 'personinfo_s2.yaml')
NORM_SCHEMA = str(INPUT_DIR / 'mapping_norm.yaml')
DENORM_SCHEMA = str(INPUT_DIR / 'mapping_denorm.yaml')
SPECIFICATION = str(INPUT_DIR / 'transform-s1-to-s2.yaml')
DENORM_SPECIFICATION = str(INPUT_DIR / 'denormalize-mapping.yaml')

def output_path(fn: str) -> str:
    return str(Path(OUTPUT_DIR) / fn)
