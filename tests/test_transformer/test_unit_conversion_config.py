"""End-to-end coverage for the ``UnitConversionConfiguration`` options.

The compliance suite exercises unit *pairs* exhaustively (14 UCUM cases) but
always with a float source value, so it says nothing about how the config's
other options behave. These drive real schemas and specs through
``map_object`` rather than poking ``_perform_unit_conversion`` with mocks.

Replaces the mock block removed in issue #298. The numeric-string and
``none_if_non_numeric`` cases guard 2fb4f12, which introduced both.
"""

import textwrap

import pytest
from linkml_runtime import SchemaView

from linkml_map.transformer.errors import TransformationError
from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/uc-source
    name: uc_source
    prefixes: {linkml: https://w3id.org/linkml/}
    imports: [linkml:types]
    default_range: string
    classes:
      Measurement:
        attributes:
          id:
            identifier: true
          length:
            range: float
            unit:
              ucum_code: cm
          length_text:
            range: string
            unit:
              ucum_code: cm
""")

TARGET_SCHEMA = textwrap.dedent("""\
    id: https://example.org/uc-target
    name: uc_target
    prefixes: {linkml: https://w3id.org/linkml/}
    imports: [linkml:types]
    default_range: string
    classes:
      FlatMeasurement:
        attributes:
          id:
            identifier: true
          length_m: {}
""")


def _transformer(unit_conversion: dict, populated_from: str = "length") -> ObjectTransformer:
    """Build a transformer whose single derived slot carries *unit_conversion*.

    :param unit_conversion: the ``unit_conversion`` block for the derived slot
    :param populated_from: source slot to convert from
    :return: a transformer ready for ``map_object``
    :rtype: ObjectTransformer
    """
    obj_tr = ObjectTransformer()
    obj_tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    obj_tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    obj_tr.create_transformer_specification(
        {
            "class_derivations": {
                "FlatMeasurement": {
                    "populated_from": "Measurement",
                    "slot_derivations": {
                        "id": {},
                        "length_m": {"populated_from": populated_from, "unit_conversion": unit_conversion},
                    },
                }
            }
        }
    )
    return obj_tr


def test_bare_magnitude_conversion() -> None:
    """Without target slots the result is a bare converted number."""
    obj_tr = _transformer({"target_unit": "m"})

    result = obj_tr.map_object({"id": "M1", "length": 120}, source_type="Measurement")

    assert result["length_m"] == pytest.approx(1.2)


def test_target_slots_emit_a_structured_value() -> None:
    """``target_magnitude_slot`` makes the result structured rather than a bare number."""
    obj_tr = _transformer(
        {"target_unit": "m", "target_magnitude_slot": "value_converted", "target_unit_slot": "unit_converted"}
    )

    result = obj_tr.map_object({"id": "M1", "length": 120}, source_type="Measurement")

    assert result["length_m"] == {"value_converted": pytest.approx(1.2), "unit_converted": "m"}


def test_source_unit_conflicting_with_the_schema_raises() -> None:
    """A declared ``source_unit`` that contradicts the slot's own unit is a spec error.

    Silently trusting either one would convert by the wrong factor.
    """
    obj_tr = _transformer({"source_unit": "mm", "target_unit": "m"})

    with pytest.raises(TransformationError, match="Mismatch in source units") as excinfo:
        obj_tr.map_object({"id": "M1", "length": 100}, source_type="Measurement")
    assert isinstance(excinfo.value.cause, ValueError)


def test_absent_source_value_yields_none() -> None:
    """A source object missing the slot converts to null rather than failing."""
    obj_tr = _transformer({"target_unit": "m"})

    result = obj_tr.map_object({"id": "M1"}, source_type="Measurement")

    assert result.get("length_m") is None


def test_numeric_string_is_converted() -> None:
    """A numeric value arriving as a string still converts (regression guard, 2fb4f12).

    Tabular sources deliver every column as text, so refusing strings here broke
    conversion for TSV input entirely.
    """
    obj_tr = _transformer({"target_unit": "m"}, populated_from="length_text")

    result = obj_tr.map_object({"id": "M1", "length_text": "120"}, source_type="Measurement")

    assert result["length_m"] == pytest.approx(1.2)


def test_non_numeric_string_raises_by_default() -> None:
    """A non-numeric value is an error unless the spec opts out (regression guard, 2fb4f12).

    Failing loudly is the point: silently nulling would corrupt a column whose
    coded values the curator never intended to convert.
    """
    obj_tr = _transformer({"target_unit": "m"}, populated_from="length_text")

    with pytest.raises(TransformationError, match="could not convert string to float") as excinfo:
        obj_tr.map_object({"id": "M1", "length_text": "A"}, source_type="Measurement")
    assert isinstance(excinfo.value.cause, ValueError)


def test_none_if_non_numeric_opts_out_of_raising() -> None:
    """``none_if_non_numeric`` is the explicit opt-in for mixed coded/numeric columns."""
    obj_tr = _transformer({"target_unit": "m", "none_if_non_numeric": True}, populated_from="length_text")

    result = obj_tr.map_object({"id": "M1", "length_text": "A"}, source_type="Measurement")

    assert result.get("length_m") is None
