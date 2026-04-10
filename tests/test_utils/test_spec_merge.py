"""Tests for the spec merge utilities."""

import pytest
import yaml

from linkml_map.utils.spec_merge import (
    load_and_merge_specs,
    load_spec_file,
    merge_spec_dicts,
    resolve_spec_paths,
)


class TestResolveSpecPaths:
    def test_single_file(self, tmp_path):
        f = tmp_path / "spec.yaml"
        f.write_text("class_derivations: {}")
        result = resolve_spec_paths((str(f),))
        assert result == [f]

    def test_directory(self, tmp_path):
        (tmp_path / "a.yaml").write_text("{}")
        (tmp_path / "b.yml").write_text("{}")
        (tmp_path / "c.txt").write_text("{}")
        result = resolve_spec_paths((str(tmp_path),))
        assert len(result) == 2
        names = {p.name for p in result}
        assert names == {"a.yaml", "b.yml"}

    def test_recursive_directory(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.yaml").write_text("{}")
        (sub / "b.yaml").write_text("{}")
        result = resolve_spec_paths((str(tmp_path),))
        assert len(result) == 2

    def test_nonexistent_path_raises(self):
        with pytest.raises(FileNotFoundError):
            resolve_spec_paths(("/no/such/path",))

    def test_mixed_file_and_dir(self, tmp_path):
        f = tmp_path / "spec.yaml"
        f.write_text("{}")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "other.yaml").write_text("{}")
        result = resolve_spec_paths((str(f), str(sub)))
        assert len(result) == 2


class TestLoadSpecFile:
    def test_dict_format(self, tmp_path):
        f = tmp_path / "spec.yaml"
        f.write_text(yaml.dump({"class_derivations": {"Foo": {"populated_from": "Bar"}}}))
        result = load_spec_file(f)
        assert len(result) == 1
        assert "class_derivations" in result[0]

    def test_list_format(self, tmp_path):
        f = tmp_path / "spec.yaml"
        content = [
            {"class_derivations": {"A": {"populated_from": "X"}}},
            {"class_derivations": {"B": {"populated_from": "Y"}}},
        ]
        f.write_text(yaml.dump(content))
        result = load_spec_file(f)
        assert len(result) == 2

    def test_non_dict_items_skipped(self, tmp_path):
        f = tmp_path / "spec.yaml"
        f.write_text("- class_derivations:\n    A:\n      populated_from: X\n- just a string\n")
        result = load_spec_file(f)
        assert len(result) == 1

    def test_scalar_yaml_returns_empty(self, tmp_path):
        f = tmp_path / "spec.yaml"
        f.write_text("just a string\n")
        result = load_spec_file(f)
        assert result == []


class TestMergeSpecDicts:
    def test_empty_list(self):
        assert merge_spec_dicts([]) == {}

    def test_single_spec(self):
        spec = {"class_derivations": [{"name": "Foo"}]}
        assert merge_spec_dicts([spec]) is spec

    def test_class_derivations_appended(self):
        s1 = {"class_derivations": [{"name": "A", "populated_from": "X"}]}
        s2 = {"class_derivations": [{"name": "B", "populated_from": "Y"}]}
        merged = merge_spec_dicts([s1, s2])
        assert len(merged["class_derivations"]) == 2

    def test_class_derivations_dict_format(self):
        s1 = {"class_derivations": {"A": {"populated_from": "X"}}}
        s2 = {"class_derivations": {"B": {"populated_from": "Y"}}}
        merged = merge_spec_dicts([s1, s2])
        assert len(merged["class_derivations"]) == 2

    def test_enum_derivations_unioned(self):
        s1 = {"enum_derivations": {"E1": {"populated_from": "SE1"}}}
        s2 = {"enum_derivations": {"E2": {"populated_from": "SE2"}}}
        merged = merge_spec_dicts([s1, s2])
        assert "E1" in merged["enum_derivations"]
        assert "E2" in merged["enum_derivations"]

    def test_enum_derivations_duplicate_same_ok(self):
        body = {"populated_from": "SE1"}
        s1 = {"enum_derivations": {"E1": body}}
        s2 = {"enum_derivations": {"E1": body}}
        merged = merge_spec_dicts([s1, s2])
        assert merged["enum_derivations"]["E1"] == body

    def test_enum_derivations_conflict_raises(self):
        s1 = {"enum_derivations": {"E1": {"populated_from": "A"}}}
        s2 = {"enum_derivations": {"E1": {"populated_from": "B"}}}
        with pytest.raises(ValueError, match="Conflicting enum_derivations"):
            merge_spec_dicts([s1, s2])

    def test_slot_derivations_unioned(self):
        s1 = {"slot_derivations": {"s1": {"populated_from": "x"}}}
        s2 = {"slot_derivations": {"s2": {"populated_from": "y"}}}
        merged = merge_spec_dicts([s1, s2])
        assert "s1" in merged["slot_derivations"]
        assert "s2" in merged["slot_derivations"]

    def test_slot_derivations_conflict_raises(self):
        s1 = {"slot_derivations": {"s1": {"populated_from": "x"}}}
        s2 = {"slot_derivations": {"s1": {"populated_from": "y"}}}
        with pytest.raises(ValueError, match="Conflicting slot_derivations"):
            merge_spec_dicts([s1, s2])

    def test_scalar_first_wins(self):
        s1 = {"title": "First", "class_derivations": []}
        s2 = {"title": "Second", "class_derivations": []}
        merged = merge_spec_dicts([s1, s2])
        assert merged["title"] == "First"

    def test_scalar_none_skipped(self):
        s1 = {"class_derivations": []}
        s2 = {"title": "Second", "class_derivations": []}
        merged = merge_spec_dicts([s1, s2])
        assert merged["title"] == "Second"

    def test_mixed_list_and_dict_class_derivations(self):
        s1 = {"class_derivations": [{"name": "A"}]}
        s2 = {"class_derivations": {"B": {"populated_from": "Y"}}}
        merged = merge_spec_dicts([s1, s2])
        assert len(merged["class_derivations"]) == 2


class TestLoadAndMergeSpecs:
    def test_single_file(self, tmp_path):
        f = tmp_path / "spec.yaml"
        f.write_text(yaml.dump({"class_derivations": {"Foo": {"populated_from": "Bar"}}}))
        merged = load_and_merge_specs((str(f),))
        assert "class_derivations" in merged

    def test_directory_of_sub_specs(self, tmp_path):
        """Simulate bdc-harmonized-variables sub-spec pattern."""
        (tmp_path / "measurement.yaml").write_text(
            yaml.dump(
                [
                    {"class_derivations": {"MeasurementObservation": {"populated_from": "t1"}}},
                    {"class_derivations": {"MeasurementObservation": {"populated_from": "t2"}}},
                ]
            )
        )
        (tmp_path / "drug.yaml").write_text(
            yaml.dump(
                [
                    {"class_derivations": {"DrugExposure": {"populated_from": "t3"}}},
                ]
            )
        )
        merged = load_and_merge_specs((str(tmp_path),))
        assert len(merged["class_derivations"]) == 3

    def test_separate_enum_file(self, tmp_path):
        """Enum file merged with class derivation file."""
        (tmp_path / "enums.yaml").write_text(yaml.dump({"enum_derivations": {"StatusEnum": {"mirror_source": True}}}))
        (tmp_path / "classes.yaml").write_text(
            yaml.dump({"class_derivations": {"Person": {"populated_from": "people"}}})
        )
        merged = load_and_merge_specs((str(tmp_path),))
        assert "StatusEnum" in merged["enum_derivations"]
        assert len(merged["class_derivations"]) == 1

    def test_no_yaml_files_raises(self, tmp_path):
        sub = tmp_path / "empty"
        sub.mkdir()
        with pytest.raises(ValueError, match="No YAML files"):
            load_and_merge_specs((str(sub),))
