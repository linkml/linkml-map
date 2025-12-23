"""Test pivot (melt/unmelt) operations."""

from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

# --- Minimal schemas for testing ---

EAV_SOURCE_SCHEMA = """
id: https://example.org/eav
name: eav-source
prefixes:
  linkml: https://w3id.org/linkml/

imports:
  - linkml:types

classes:
  Measurement:
    attributes:
      att:
        range: string
      val:
        range: float
      unit:
        range: string
        required: false

  MeasurementContainer:
    tree_root: true
    attributes:
      id:
        range: string
      measurements:
        range: Measurement
        multivalued: true
        inlined: true
"""

WIDE_TARGET_SCHEMA = """
id: https://example.org/wide
name: wide-target
prefixes:
  linkml: https://w3id.org/linkml/

imports:
  - linkml:types

classes:
  WideRecord:
    tree_root: true
    attributes:
      id:
        range: string
      height:
        range: float
      weight:
        range: float
      height_m:
        range: float
      weight_kg:
        range: float
      len_m:
        range: float
"""

WIDE_SOURCE_SCHEMA = """
id: https://example.org/wide-source
name: wide-source
prefixes:
  linkml: https://w3id.org/linkml/

imports:
  - linkml:types

classes:
  WideRecord:
    tree_root: true
    attributes:
      id:
        range: string
      height:
        range: float
      weight:
        range: float
      # Placeholder for MELT tests - the measurements slot is derived via pivot
      measurements:
        range: string
        multivalued: true
"""

EAV_TARGET_SCHEMA = """
id: https://example.org/eav-target
name: eav-target
prefixes:
  linkml: https://w3id.org/linkml/

imports:
  - linkml:types

classes:
  MeasurementResult:
    tree_root: true
    attributes:
      id:
        range: string
      measurements:
        range: Measurement
        multivalued: true
        inlined: true

  Measurement:
    attributes:
      variable:
        range: string
      value:
        range: float
"""


class TestUnmeltBasic:
    """Test UNMELT operation: EAV to wide format."""

    def test_unmelt_single_record(self) -> None:
        """Single EAV record transforms to wide format slot."""
        source_sv = SchemaView(EAV_SOURCE_SCHEMA)
        target_sv = SchemaView(WIDE_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "WideRecord": {
                    "populated_from": "Measurement",
                    "pivot_operation": {
                        "direction": "UNMELT",
                        "variable_slot": "att",
                        "value_slot": "val",
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        source_obj = {"att": "height", "val": 1.8}
        result = obj_tr.map_object(source_obj, source_type="Measurement")

        assert result == {"height": 1.8}

    def test_unmelt_collection(self) -> None:
        """Collection of EAV records transforms to single wide object."""
        source_sv = SchemaView(EAV_SOURCE_SCHEMA)
        target_sv = SchemaView(WIDE_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "WideRecord": {
                    "populated_from": "MeasurementContainer",
                    "pivot_operation": {
                        "direction": "UNMELT",
                        "variable_slot": "att",
                        "value_slot": "val",
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        source_obj = {
            "id": "container1",
            "measurements": [
                {"att": "height", "val": 1.8},
                {"att": "weight", "val": 75.0},
            ],
        }
        result = obj_tr.map_object(source_obj, source_type="MeasurementContainer")

        assert result == {"height": 1.8, "weight": 75.0}


class TestUnmeltWithUnit:
    """Test UNMELT with unit-aware slot naming."""

    def test_unmelt_with_unit_template(self) -> None:
        """EAV with unit transforms to slot name with unit suffix."""
        source_sv = SchemaView(EAV_SOURCE_SCHEMA)
        target_sv = SchemaView(WIDE_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "WideRecord": {
                    "populated_from": "Measurement",
                    "pivot_operation": {
                        "direction": "UNMELT",
                        "variable_slot": "att",
                        "value_slot": "val",
                        "unit_slot": "unit",
                        "slot_name_template": "{variable}_{unit}",
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        source_obj = {"att": "len", "val": 1.0, "unit": "m"}
        result = obj_tr.map_object(source_obj, source_type="Measurement")

        assert result == {"len_m": 1.0}

    def test_unmelt_collection_with_units(self) -> None:
        """Collection of EAV records with units transforms correctly."""
        source_sv = SchemaView(EAV_SOURCE_SCHEMA)
        target_sv = SchemaView(WIDE_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "WideRecord": {
                    "populated_from": "MeasurementContainer",
                    "pivot_operation": {
                        "direction": "UNMELT",
                        "variable_slot": "att",
                        "value_slot": "val",
                        "unit_slot": "unit",
                        "slot_name_template": "{variable}_{unit}",
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        source_obj = {
            "measurements": [
                {"att": "height", "val": 1.8, "unit": "m"},
                {"att": "weight", "val": 75.0, "unit": "kg"},
            ],
        }
        result = obj_tr.map_object(source_obj, source_type="MeasurementContainer")

        assert result == {"height_m": 1.8, "weight_kg": 75.0}


class TestMeltBasic:
    """Test MELT operation: wide to EAV format."""

    def test_melt_basic(self) -> None:
        """Wide format transforms to EAV records."""
        source_sv = SchemaView(WIDE_SOURCE_SCHEMA)
        target_sv = SchemaView(EAV_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "MeasurementResult": {
                    "populated_from": "WideRecord",
                    "slot_derivations": {
                        "id": {"populated_from": "id"},
                        "measurements": {
                            "pivot_operation": {
                                "direction": "MELT",
                                "variable_slot": "variable",
                                "value_slot": "value",
                                "source_slots": ["height", "weight"],
                                "id_slots": ["id"],
                            }
                        },
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        source_obj = {"id": "p1", "height": 1.8, "weight": 75.0}
        result = obj_tr.map_object(source_obj, source_type="WideRecord")

        assert result["id"] == "p1"
        assert len(result["measurements"]) == 2

        # Sort by variable name for consistent comparison
        measurements = sorted(result["measurements"], key=lambda x: x["variable"])
        # id_slots includes 'id', so each record has it
        assert measurements[0] == {"id": "p1", "variable": "height", "value": 1.8}
        assert measurements[1] == {"id": "p1", "variable": "weight", "value": 75.0}

    def test_melt_with_id_slots(self) -> None:
        """MELT operation preserves id_slots in each record."""
        source_sv = SchemaView(WIDE_SOURCE_SCHEMA)
        target_sv = SchemaView(EAV_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "MeasurementResult": {
                    "populated_from": "WideRecord",
                    "slot_derivations": {
                        "measurements": {
                            "pivot_operation": {
                                "direction": "MELT",
                                "variable_slot": "variable",
                                "value_slot": "value",
                                "source_slots": ["height", "weight"],
                                "id_slots": ["id"],
                            }
                        },
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        source_obj = {"id": "p1", "height": 1.8, "weight": 75.0}
        result = obj_tr.map_object(source_obj, source_type="WideRecord")

        # Each melted record should have the id
        for measurement in result["measurements"]:
            assert measurement.get("id") == "p1"


class TestEdgeCases:
    """Test edge cases for pivot operations."""

    def test_unmelt_missing_value(self) -> None:
        """UNMELT handles missing value gracefully."""
        source_sv = SchemaView(EAV_SOURCE_SCHEMA)
        target_sv = SchemaView(WIDE_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "WideRecord": {
                    "populated_from": "Measurement",
                    "pivot_operation": {
                        "direction": "UNMELT",
                        "variable_slot": "att",
                        "value_slot": "val",
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        # Missing value slot
        source_obj = {"att": "height"}
        result = obj_tr.map_object(source_obj, source_type="Measurement")

        assert result == {"height": None}

    def test_unmelt_missing_variable(self) -> None:
        """UNMELT handles missing variable gracefully."""
        source_sv = SchemaView(EAV_SOURCE_SCHEMA)
        target_sv = SchemaView(WIDE_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "WideRecord": {
                    "populated_from": "Measurement",
                    "pivot_operation": {
                        "direction": "UNMELT",
                        "variable_slot": "att",
                        "value_slot": "val",
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        # Missing variable slot - should return empty dict
        source_obj = {"val": 1.8}
        result = obj_tr.map_object(source_obj, source_type="Measurement")

        assert result == {}

    def test_melt_null_values_skipped(self) -> None:
        """MELT skips slots with null values."""
        source_sv = SchemaView(WIDE_SOURCE_SCHEMA)
        target_sv = SchemaView(EAV_TARGET_SCHEMA)

        transform_spec = {
            "class_derivations": {
                "MeasurementResult": {
                    "populated_from": "WideRecord",
                    "slot_derivations": {
                        "measurements": {
                            "pivot_operation": {
                                "direction": "MELT",
                                "variable_slot": "variable",
                                "value_slot": "value",
                                "source_slots": ["height", "weight"],
                            }
                        },
                    },
                }
            }
        }

        obj_tr = ObjectTransformer()
        obj_tr.source_schemaview = source_sv
        obj_tr.target_schemaview = target_sv
        obj_tr.create_transformer_specification(transform_spec)

        # weight is None, should be skipped
        source_obj = {"height": 1.8, "weight": None}
        result = obj_tr.map_object(source_obj, source_type="WideRecord")

        assert len(result["measurements"]) == 1
        assert result["measurements"][0] == {"variable": "height", "value": 1.8}
