from linkml_runtime import SchemaView
from pathlib import Path
import pytest
from tests.scaffold import (SOURCE_SCHEMA, TARGET_SCHEMA, TRANSFORM_SPEC, INPUT_DATA, EXPECTED_DATA)
from typing import Callable
import yaml

def yaml_load(file_path: Path) -> dict:
    return yaml.safe_load(file_path.read_text())

class StrictDict(dict):
    """A dict that disallows overwriting with a different value."""

    def __setitem__(self, key, value):
        """Set an item, disallowing overwrites with different values."""
        if key in self and self[key] != value:
            raise ValueError(
                f"Duplicate assignment to expected key '{key}': "
                f"existing={self[key]!r}, new={value!r}"
            )
        super().__setitem__(key, value)

    def update(self, *args, **kwargs):
        """Update the dictionary, disallowing overwrites with different values."""
        other = dict(*args, **kwargs)
        for key, value in other.items():
            self[key] = value

@pytest.fixture
def scaffold():
    """Fresh scaffold per test."""
    return {
        "source_schema": SchemaView(SOURCE_SCHEMA),
        "target_schema": SchemaView(TARGET_SCHEMA),
        "transform_spec": yaml_load(TRANSFORM_SPEC),
        "input_data": yaml_load(INPUT_DATA),
        "expected": StrictDict(yaml_load(EXPECTED_DATA)),
    }

# Global registry to collect setup functions for unit parameterization and integration scaffolds.
# They are *not* tests, so pytest cannot discover them automatically.
TEST_SETUP_FUNCTIONS = []

def add_to_test_setup(func: Callable) -> Callable:
    """Decorator to register a setup function for test scaffold."""
    TEST_SETUP_FUNCTIONS.append(func)
    return func

@pytest.fixture
def integration_scaffold(scaffold):
    """Return a scaffold with all registered integration setup functions applied."""
    for setup_func in TEST_SETUP_FUNCTIONS:
        setup_func(scaffold)
    return scaffold
