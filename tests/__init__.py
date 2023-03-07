import os
from pathlib import Path

from linkml_runtime.linkml_model import SchemaDefinition

SRC = "source"
TGT = "target"
TR = "transform"
DATA = "data"

ROOT = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = Path(ROOT) / "input"
OUTPUT_DIR = Path(ROOT) / "output"
EXAMPLE_DIR = Path(INPUT_DIR) / "examples"

PERSONINFO_BASIC_EXAMPLE_DIR = Path(EXAMPLE_DIR) / "personinfo_basic"
PERSONINFO_SRC_SCHEMA = PERSONINFO_BASIC_EXAMPLE_DIR / SRC / "personinfo.yaml"
PERSONINFO_TGT_SCHEMA = PERSONINFO_BASIC_EXAMPLE_DIR / TGT / "agent.yaml"
PERSONINFO_TR = PERSONINFO_BASIC_EXAMPLE_DIR / TR / "personinfo-to-agent.transform.yaml"
PERSONINFO_DATA = PERSONINFO_BASIC_EXAMPLE_DIR / DATA / "Person-001.yaml"
PERSONINFO_CONTAINER_DATA = PERSONINFO_BASIC_EXAMPLE_DIR / DATA / "Container-001.yaml"

FLATTENING_BASIC_EXAMPLE_DIR = Path(EXAMPLE_DIR) / "flattening"
FLATTENING_SRC_SCHEMA = FLATTENING_BASIC_EXAMPLE_DIR / SRC / "normalized.yaml"
FLATTENING_TGT_SCHEMA = FLATTENING_BASIC_EXAMPLE_DIR / TGT / "denormalized.yaml"
FLATTENING_TR = FLATTENING_BASIC_EXAMPLE_DIR / TR / "denormalize.transform.yaml"
FLATTENING_DATA = FLATTENING_BASIC_EXAMPLE_DIR / DATA / "MappingSet-001.yaml"

BIOLINK_BASIC_EXAMPLE_DIR = Path(EXAMPLE_DIR) / "biolink"
BIOLINK_SRC_SCHEMA = BIOLINK_BASIC_EXAMPLE_DIR / SRC / "biolink.yaml"
BIOLINK_TGT_SCHEMA = BIOLINK_BASIC_EXAMPLE_DIR / TGT / "monarch.yaml"
BIOLINK_TR = BIOLINK_BASIC_EXAMPLE_DIR / TR / "biolink-example-profile.transform.yaml"
BIOLINK_DATA = BIOLINK_BASIC_EXAMPLE_DIR / DATA / "Association-001.yaml"


# TODO: migrate these to example dir
SCHEMA1 = str(PERSONINFO_SRC_SCHEMA)
SCHEMA2 = str(PERSONINFO_TGT_SCHEMA)
SPECIFICATION = str(PERSONINFO_TR)

NORM_SCHEMA = str(FLATTENING_SRC_SCHEMA)
DENORM_SCHEMA = str(FLATTENING_TGT_SCHEMA)
DENORM_SPECIFICATION = str(FLATTENING_TR)


def output_path(fn: str) -> str:
    return str(Path(OUTPUT_DIR) / fn)