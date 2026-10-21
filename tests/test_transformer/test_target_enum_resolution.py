"""Enum-ranged slot values resolve to the target enum's permissible value keys (#360).

A spec may spell a permissible value by its key, ``meaning``, ``title`` or an alias;
the output always carries the key.
"""

import logging

import pytest
from linkml_runtime import SchemaView

from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.utils.enum_index import enum_index
from tests.conftest import make_setup_registry, run_transformer, setup_ids
from tests.scaffold.utils.apply_patch import apply_schema_patch, apply_transform_patch

ENUM_SETUPS, add_to_test_setup = make_setup_registry()

SEX_ENUM_PATCH = """
prefixes:
  OMOP:
    prefix_reference: https://athena.ohdsi.org/search-terms/terms/
enums:
  SexEnum:
    permissible_values:
      "OMOP:8532":
        title: FEMALE
        meaning: OMOP:8532
        aliases: [F, female]
      "OMOP:8507":
        title: MALE
        meaning: OMOP:8507
        aliases: [M, male]
"""


def _add_sex_enum(scaffold: dict, slot: str, *, multivalued: bool = False) -> None:
    if "SexEnum" not in scaffold["target_schema"].schema.enums:
        apply_schema_patch(scaffold["target_schema"], SEX_ENUM_PATCH)
    apply_schema_patch(
        scaffold["target_schema"],
        f"""
    classes:
      Agent:
        attributes:
          {slot}:
            range: SexEnum
            multivalued: {str(multivalued).lower()}
""",
    )


@add_to_test_setup
def setup_value_mapping_target_by_title(scaffold):
    """A value_mappings target spelled as the title resolves to the key."""
    _add_sex_enum(scaffold, "sex")
    apply_schema_patch(
        scaffold["source_schema"],
        """
    classes:
      Person:
        attributes:
          gender:
            range: string
""",
    )
    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          sex:
            populated_from: gender
            value_mappings:
              f: FEMALE
              m: MALE
""",
    )
    scaffold["input_data"]["gender"] = "f"
    scaffold["expected"]["sex"] = "OMOP:8532"


@add_to_test_setup
def setup_value_literal_by_expanded_meaning(scaffold):
    """A value literal written as the full URI matches the meaning CURIE."""
    _add_sex_enum(scaffold, "sex_literal")
    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          sex_literal:
            value: https://athena.ohdsi.org/search-terms/terms/8507
""",
    )
    scaffold["expected"]["sex_literal"] = "OMOP:8507"


@add_to_test_setup
def setup_expr_result_by_alias(scaffold):
    """An expr result spelled as an alias resolves to the key."""
    _add_sex_enum(scaffold, "sex_expr")
    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          sex_expr:
            expr: "case(({id} == 'P:001', 'female'), (True, 'male'))"
""",
    )
    scaffold["expected"]["sex_expr"] = "OMOP:8532"


@add_to_test_setup
def setup_multivalued_resolves_each_element(scaffold):
    """Each element of a multivalued enum slot resolves on its own."""
    _add_sex_enum(scaffold, "sexes", multivalued=True)
    apply_schema_patch(
        scaffold["source_schema"],
        """
    classes:
      Person:
        attributes:
          genders:
            range: string
            multivalued: true
""",
    )
    apply_transform_patch(
        scaffold["transform_spec"],
        """
    class_derivations:
      Agent:
        slot_derivations:
          sexes:
            populated_from: genders
""",
    )
    scaffold["input_data"]["genders"] = ["F", "OMOP:8507", "FEMALE"]
    scaffold["expected"]["sexes"] = ["OMOP:8532", "OMOP:8507", "OMOP:8532"]


@pytest.mark.parametrize("setup_func", ENUM_SETUPS, ids=setup_ids(ENUM_SETUPS))
def test_unit(scaffold, setup_func):
    """Apply a setup function, run transformer, and assert expected output."""
    setup_func(scaffold)
    result = run_transformer(scaffold)
    assert result == scaffold["expected"]


def _transformer(
    scaffold: dict, value: str, *, strict: bool, enum_patch: str = SEX_ENUM_PATCH, spec_range: str | None = None
) -> ObjectTransformer:
    apply_schema_patch(scaffold["target_schema"], enum_patch)
    apply_schema_patch(
        scaffold["target_schema"],
        """
    classes:
      Agent:
        attributes:
          sex:
            range: SexEnum
""",
    )
    apply_transform_patch(
        scaffold["transform_spec"],
        f"""
    class_derivations:
      Agent:
        slot_derivations:
          sex:
            value: "{value}"
""",
    )
    if spec_range:
        scaffold["transform_spec"]["class_derivations"]["Agent"]["slot_derivations"]["sex"]["range"] = spec_range
    tr = ObjectTransformer(strict=strict)
    tr.source_schemaview = scaffold["source_schema"]
    tr.target_schemaview = scaffold["target_schema"]
    tr.create_transformer_specification(scaffold["transform_spec"])
    return tr


def test_unmatched_value_warns_once_and_passes_through(scaffold, caplog):
    """Outside strict mode an unknown spelling is kept, with one warning however many rows."""
    tr = _transformer(scaffold, "unknown", strict=False)
    with caplog.at_level(logging.WARNING):
        results = [tr.map_object(scaffold["input_data"], source_type="Person") for _ in range(3)]
    assert [r["sex"] for r in results] == ["unknown"] * 3
    warnings = [r.message for r in caplog.records if "permissible value" in r.message]
    assert warnings == ["'unknown' is not a permissible value of enum SexEnum"]


def test_unmatched_value_raises_in_strict_mode(scaffold):
    """In strict mode an unknown spelling fails the row."""
    tr = _transformer(scaffold, "unknown", strict=True)
    with pytest.raises(TransformationError, match="'unknown' is not a permissible value of enum SexEnum"):
        tr.map_object(scaffold["input_data"], source_type="Person")


AMBIGUOUS_TITLE_PATCH = """
enums:
  SexEnum:
    permissible_values:
      F1:
        title: FEMALE
      F2:
        title: FEMALE
"""


def test_ambiguous_value_raises_in_strict_mode(scaffold):
    """A spelling shared by two permissible values in the same tier can't be resolved."""
    tr = _transformer(scaffold, "FEMALE", strict=True, enum_patch=AMBIGUOUS_TITLE_PATCH)
    with pytest.raises(TransformationError, match=r"matches more than one permissible value .*\['F1', 'F2'\]"):
        tr.map_object(scaffold["input_data"], source_type="Person")


KEY_SHADOWS_TITLE_PATCH = """
enums:
  SexEnum:
    permissible_values:
      FEMALE:
        title: female (legacy)
      "OMOP:8532":
        title: FEMALE
"""


def test_key_wins_over_another_values_title(scaffold):
    """A value that is a key resolves to itself, even if another value uses it as a title."""
    tr = _transformer(scaffold, "FEMALE", strict=True, enum_patch=KEY_SHADOWS_TITLE_PATCH)
    assert tr.map_object(scaffold["input_data"], source_type="Person")["sex"] == "FEMALE"


def test_spec_range_overrides_target_enum(scaffold):
    """An explicit non-enum range on the derivation turns resolution off."""
    tr = _transformer(scaffold, "female", strict=True, spec_range="string")
    assert tr.map_object(scaffold["input_data"], source_type="Person")["sex"] == "female"


@pytest.mark.parametrize(
    "enum_yaml",
    [
        "Dynamic:\n    reachable_from:\n      source_ontology: obo:mondo\n      source_nodes: [MONDO:0000001]",
        "Dynamic:\n    description: no permissible values",
    ],
    ids=["reachable_from", "empty"],
)
def test_open_enums_have_no_index(enum_yaml):
    """Enums without a closed list of permissible values are left unresolved."""
    sv = SchemaView(f"id: https://example.org/e\nname: e\nenums:\n  {enum_yaml}\n")
    assert enum_index(sv, "Dynamic") is None
