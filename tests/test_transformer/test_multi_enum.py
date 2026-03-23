"""Tests for enum mapping on slots with multiple enum ranges via any_of.

Verifies that when a source slot uses ``any_of`` to specify multiple enum
ranges, the transformer correctly iterates enum derivations in order and
maps permissible values across all enums.

See: https://github.com/linkml/linkml-map/issues/146
     https://github.com/linkml/linkml/issues/2128
"""

import copy

import pytest
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = """\
id: https://example.org/lights-source
name: lights-source
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
enums:
  PrimaryColors:
    permissible_values:
      light_red:
      dark_red:
      light_green:
      dark_green:
      light_blue:
      dark_blue:
  SecondaryColors:
    permissible_values:
      light_cyan:
      dark_cyan:
      light_magenta:
      dark_magenta:
  Missingness:
    permissible_values:
      not_available:
      other:
classes:
  Light:
    attributes:
      id:
        identifier: true
        range: string
      color:
        any_of:
          - range: PrimaryColors
          - range: SecondaryColors
          - range: Missingness
      colors:
        multivalued: true
        any_of:
          - range: PrimaryColors
          - range: SecondaryColors
          - range: Missingness
  Container:
    tree_root: true
    attributes:
      lights:
        range: Light
        multivalued: true
        inlined_as_list: true
"""

TARGET_SCHEMA = """\
id: https://example.org/lights-target
name: lights-target
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
enums:
  SimplePrimary:
    permissible_values:
      red:
      green:
      blue:
  SimpleSecondary:
    permissible_values:
      cyan:
      magenta:
  MissingnessTarget:
    permissible_values:
      na:
      oth:
classes:
  Light:
    attributes:
      id:
        identifier: true
        range: string
      color:
        any_of:
          - range: SimplePrimary
          - range: SimpleSecondary
          - range: MissingnessTarget
      colors:
        multivalued: true
        any_of:
          - range: SimplePrimary
          - range: SimpleSecondary
          - range: MissingnessTarget
  Container:
    tree_root: true
    attributes:
      lights:
        range: Light
        multivalued: true
        inlined_as_list: true
"""

TRANSFORM_SPEC = {
    "class_derivations": {
        "Light": {
            "populated_from": "Light",
            "slot_derivations": {
                "id": {},
                "color": {"populated_from": "color"},
                "colors": {"populated_from": "colors"},
            },
        },
        "Container": {
            "populated_from": "Container",
            "slot_derivations": {
                "lights": {"populated_from": "lights"},
            },
        },
    },
    "enum_derivations": {
        "SimplePrimary": {
            "name": "SimplePrimary",
            "populated_from": "PrimaryColors",
            "permissible_value_derivations": {
                "red": {
                    "name": "red",
                    "sources": ["light_red", "dark_red"],
                },
                "green": {
                    "name": "green",
                    "sources": ["light_green", "dark_green"],
                },
                "blue": {
                    "name": "blue",
                    "sources": ["light_blue", "dark_blue"],
                },
            },
        },
        "SimpleSecondary": {
            "name": "SimpleSecondary",
            "populated_from": "SecondaryColors",
            "permissible_value_derivations": {
                "cyan": {
                    "name": "cyan",
                    "sources": ["light_cyan", "dark_cyan"],
                },
                "magenta": {
                    "name": "magenta",
                    "sources": ["light_magenta", "dark_magenta"],
                },
            },
        },
        "MissingnessTarget": {
            "name": "MissingnessTarget",
            "populated_from": "Missingness",
            "permissible_value_derivations": {
                "na": {
                    "name": "na",
                    "populated_from": "not_available",
                },
                "oth": {
                    "name": "oth",
                    "populated_from": "other",
                },
            },
        },
    },
}


def _make_transformer() -> ObjectTransformer:
    """Build an ObjectTransformer wired to the source/target schemas and spec."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(copy.deepcopy(TRANSFORM_SPEC))
    return tr


@pytest.mark.parametrize(
    "source_color,expected",
    [
        ("light_red", "red"),
        ("dark_red", "red"),
        ("light_green", "green"),
        ("dark_blue", "blue"),
        ("light_cyan", "cyan"),
        ("dark_magenta", "magenta"),
        ("not_available", "na"),
        ("other", "oth"),
    ],
    ids=[
        "primary-light_red",
        "primary-dark_red",
        "primary-light_green",
        "primary-dark_blue",
        "secondary-light_cyan",
        "secondary-dark_magenta",
        "missingness-not_available",
        "missingness-other",
    ],
)
def test_single_valued_multi_enum(source_color, expected):
    """Single-valued slot with any_of enum ranges maps correctly."""
    tr = _make_transformer()
    source = {"id": "light1", "color": source_color}
    result = tr.map_object(source, source_type="Light")
    assert result["color"] == expected


def test_multivalued_multi_enum():
    """Multivalued slot with any_of enum ranges maps all values."""
    tr = _make_transformer()
    source = {
        "id": "light1",
        "colors": ["light_red", "dark_green", "light_magenta", "not_available"],
    }
    result = tr.map_object(source, source_type="Light")
    assert result["colors"] == ["red", "green", "magenta", "na"]


def test_no_matching_enum_returns_none():
    """Value not in any enum derivation returns None."""
    tr = _make_transformer()
    source = {"id": "light1", "color": "nonexistent_value"}
    result = tr.map_object(source, source_type="Light")
    assert result["color"] is None


def test_container_with_multi_enum():
    """End-to-end: container with nested objects using multi-enum slots."""
    tr = _make_transformer()
    source = {
        "lights": [
            {
                "id": "l1",
                "color": "light_red",
                "colors": ["light_red", "dark_green", "not_available"],
            },
            {
                "id": "l2",
                "color": "light_cyan",
                "colors": ["light_magenta"],
            },
        ],
    }
    result = tr.map_object(source, source_type="Container")
    assert result["lights"][0]["color"] == "red"
    assert result["lights"][0]["colors"] == ["red", "green", "na"]
    assert result["lights"][1]["color"] == "cyan"
    assert result["lights"][1]["colors"] == ["magenta"]


def test_mirror_source_stops_iteration():
    """mirror_source on an earlier enum prevents trying later enums."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)

    spec = copy.deepcopy(TRANSFORM_SPEC)
    # Set mirror_source on PrimaryColors derivation
    spec["enum_derivations"]["SimplePrimary"]["mirror_source"] = True
    tr.create_transformer_specification(spec)

    # "unknown_value" doesn't match any PrimaryColors PV derivation,
    # but mirror_source=True means it returns unchanged
    source = {"id": "light1", "color": "unknown_value"}
    result = tr.map_object(source, source_type="Light")
    assert result["color"] == "unknown_value"


def test_null_color_stays_none():
    """Null source value is not transformed."""
    tr = _make_transformer()
    source = {"id": "light1", "color": None}
    result = tr.map_object(source, source_type="Light")
    assert result["color"] is None


def test_explicit_range_any_with_any_of():
    """Slots with explicit range: Any plus any_of enum ranges are mapped correctly."""
    schema = SOURCE_SCHEMA.replace(
        "      color:\n        any_of:",
        "      color:\n        range: Any\n        any_of:",
    )
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(schema)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(copy.deepcopy(TRANSFORM_SPEC))

    source = {"id": "light1", "color": "light_red"}
    result = tr.map_object(source, source_type="Light")
    assert result["color"] == "red"
