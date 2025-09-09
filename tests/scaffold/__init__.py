import copy

# --- Minimal Transform Spec ---
SCAFFOLD_TRANSFORM = {
    "class_derivations": {}
}

# --- Minimal Example Data ---
SOURCE_SCAFFOLD_DATA = {
    "id": "P:001",
    "name": "fred bloggs"
}

# --- Minimal Example Data ---
TARGET_SCAFFOLD_DATA = {
    "id": "P:001",
    "label": "fred bloggs"
}


def make_scaffold():
    """Return a fresh scaffold copy for a single test."""
    return {
        "src_schema": copy.deepcopy(SOURCE_SCAFFOLD_SCHEMA),
        "tgt_schema": copy.deepcopy(TARGET_SCAFFOLD_SCHEMA),
        "transform_spec": copy.deepcopy(SCAFFOLD_TRANSFORM),
        "person_data": copy.deepcopy(SOURCE_SCAFFOLD_DATA),
        "expected": copy.deepcopy(TARGET_SCAFFOLD_DATA),
    }
