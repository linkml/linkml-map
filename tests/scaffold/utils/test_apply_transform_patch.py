import pytest
from tests.scaffold.utils.apply_patch import apply_transform_patch

def test_apply_transform_patch_merges_dicts():
    transform = {
        "class_derivations": {
            "Agent": {
                "slot_derivations": {
                    "name": {"value": "Alice"}
                }
            }
        }
    }

    patch = """
class_derivations:
  Agent:
    slot_derivations:
      age:
        value: 30
"""

    expected = {
        "class_derivations": {
            "Agent": {
                "slot_derivations": {
                    "name": {"value": "Alice"},
                    "age": {"value": 30},
                }
            }
        }
    }

    result = apply_transform_patch(transform, patch)
    assert result == expected

def test_apply_transform_patch_overwrites_scalar():
    transform = {"key": "old"}
    patch = "key: new"
    result = apply_transform_patch(transform, patch)
    assert result["key"] == "new"

def test_apply_transform_patch_extends_list():
    transform = {"items": [1, 2]}
    patch = "items:\n  - 3\n  - 4"
    result = apply_transform_patch(transform, patch)
    assert result["items"] == [1, 2, 3, 4]

def test_apply_transform_patch_empty_patch():
    transform = {"key": "value"}
    patch = ""
    result = apply_transform_patch(transform, patch)
    assert result == transform
