"""Tests for deprecated fields and their warnings."""

import warnings

from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = """\
id: https://example.org/source
name: source
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Person:
    attributes:
      name:
        range: string
      given_name:
        range: string
      family_name:
        range: string
"""

TARGET_SCHEMA = """\
id: https://example.org/target
name: target
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Person:
    attributes:
      name:
        range: string
      full_name:
        range: string
"""


def test_derived_from_emits_deprecation_warning():
    """Using derived_from on a SlotDerivation emits a DeprecationWarning."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    spec = {
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "slot_derivations": {
                    "full_name": {
                        "expr": '"{given_name} {family_name}"',
                        "derived_from": ["given_name", "family_name"],
                    },
                },
            },
        },
    }
    tr.create_transformer_specification(spec)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        # Trigger induce_missing_values via derived_specification
        _ = tr.derived_specification

    deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecation_warnings) == 1
    assert "derived_from" in str(deprecation_warnings[0].message)
    assert "full_name" in str(deprecation_warnings[0].message)


def test_derived_from_does_not_affect_transformation():
    """derived_from is ignored by the runtime — transformation works without it."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    spec = {
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "slot_derivations": {
                    "name": {"populated_from": "name"},
                    "full_name": {
                        "expr": '"{given_name} {family_name}"',
                        "derived_from": ["given_name", "family_name"],
                    },
                },
            },
        },
    }
    tr.create_transformer_specification(spec)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = tr.map_object(
            {"name": "Jane Doe", "given_name": "Jane", "family_name": "Doe"},
            source_type="Person",
        )

    assert result["name"] == "Jane Doe"


def test_sources_on_pv_emits_deprecation_warning():
    """Using sources on a PermissibleValueDerivation emits a DeprecationWarning."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    spec = {
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "slot_derivations": {"name": {"populated_from": "name"}},
            },
        },
        "enum_derivations": {
            "TargetEnum": {
                "populated_from": "SourceEnum",
                "permissible_value_derivations": {
                    "combined": {
                        "name": "combined",
                        "sources": ["val_a", "val_b"],
                    },
                },
            },
        },
    }
    tr.create_transformer_specification(spec)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ = tr.derived_specification

    deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    sources_warnings = [w for w in deprecation_warnings if "sources" in str(w.message)]
    assert len(sources_warnings) == 1
    assert "combined" in str(sources_warnings[0].message)


def test_sources_on_slot_emits_deprecation_warning():
    """Using sources on a SlotDerivation emits a DeprecationWarning."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    spec = {
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "slot_derivations": {
                    "name": {
                        "sources": ["name", "given_name"],
                    },
                },
            },
        },
    }
    tr.create_transformer_specification(spec)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ = tr.derived_specification

    deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    sources_warnings = [w for w in deprecation_warnings if "sources" in str(w.message)]
    assert len(sources_warnings) == 1
    assert "name" in str(sources_warnings[0].message)


def test_no_warning_without_derived_from():
    """No deprecation warning when derived_from is not used."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    spec = {
        "class_derivations": {
            "Person": {
                "populated_from": "Person",
                "slot_derivations": {
                    "name": {"populated_from": "name"},
                },
            },
        },
    }
    tr.create_transformer_specification(spec)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ = tr.derived_specification

    deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecation_warnings) == 0
