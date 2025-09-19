import pytest
from tests.conftest import StrictDict

def test_strictdict_allows_same_value():
    d = StrictDict()
    d["x"] = 1
    d["x"] = 1  # ok
    assert d["x"] == 1

def test_strictdict_rejects_conflicting_value():
    d = StrictDict()
    d["x"] = 1
    with pytest.raises(ValueError):
        d["x"] = 2

def test_strictdict_update_respects_strictness():
    d = StrictDict()
    d["x"] = 1
    d.update({"x": 1, "y": 2})
    assert d == {"x": 1, "y": 2}

    with pytest.raises(ValueError):
        d.update({"x": 99})
