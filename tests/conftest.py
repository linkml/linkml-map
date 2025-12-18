from linkml_runtime import SchemaView
from pathlib import Path
import pytest
from tests.scaffold import (SOURCE_SCHEMA, TARGET_SCHEMA, TRANSFORM_SPEC, INPUT_DATA, EXPECTED_DATA)
from tests.scaffold_container import (
    SOURCE_SCHEMA as CONTAINER_SOURCE_SCHEMA,
    TARGET_SCHEMA as CONTAINER_TARGET_SCHEMA,
    TRANSFORM_SPEC as CONTAINER_TRANSFORM_SPEC,
    INPUT_DATA as CONTAINER_INPUT_DATA,
    EXPECTED_DATA as CONTAINER_EXPECTED_DATA,
)
from typing import Callable
import yaml

def yaml_load(file_path: Path) -> dict:
    return yaml.safe_load(file_path.read_text())


def make_scaffold(source, target, transform, input_data, expected):
    """Create a scaffold dict from schema/data paths."""
    return {
        "source_schema": SchemaView(source),
        "target_schema": SchemaView(target),
        "transform_spec": yaml_load(transform),
        "input_data": yaml_load(input_data),
        "expected": StrictDict(yaml_load(expected)),
    }


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
    return make_scaffold(
        SOURCE_SCHEMA, TARGET_SCHEMA, TRANSFORM_SPEC, INPUT_DATA, EXPECTED_DATA
    )


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


@pytest.fixture
def container_scaffold():
    """Fresh container scaffold for cross-class FK tests."""
    return make_scaffold(
        CONTAINER_SOURCE_SCHEMA,
        CONTAINER_TARGET_SCHEMA,
        CONTAINER_TRANSFORM_SPEC,
        CONTAINER_INPUT_DATA,
        CONTAINER_EXPECTED_DATA,
    )


CONTAINER_TEST_SETUP_FUNCTIONS = []

def add_to_container_test_setup(func: Callable) -> Callable:
    """Decorator to register a setup function for container scaffold."""
    CONTAINER_TEST_SETUP_FUNCTIONS.append(func)
    return func

@pytest.fixture
def integration_container_scaffold(container_scaffold):
    """Return a container scaffold with all registered setup functions applied."""
    for setup_func in CONTAINER_TEST_SETUP_FUNCTIONS:
        setup_func(container_scaffold)
    return container_scaffold
