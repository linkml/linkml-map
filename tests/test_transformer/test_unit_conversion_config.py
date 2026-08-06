"""Scaffold-based coverage for the ``UnitConversionConfiguration`` options.

The compliance suite exercises unit *pairs* exhaustively (14 UCUM cases) but
always with a float source value, so it says nothing about how the config's
other options behave.

The successful conversions are registered setups, so they run both in isolation
and cumulatively in ``test_integration`` alongside every other scaffold feature.
The two error cases stay unregistered: a setup that raises would break the
cumulative run for every feature, not just its own.

Replaces the mock block removed in issue #298. The numeric-string and
``none_if_non_numeric`` cases guard 2fb4f12, which introduced both.
"""

import pytest

from linkml_map.transformer.errors import TransformationError
from tests.conftest import make_setup_registry, run_transformer, setup_ids
from tests.scaffold.utils.apply_patch import apply_schema_patch, apply_transform_patch

#: Setups owned by this module. Registering also feeds the shared integration list.
UNIT_CONVERSION_SETUPS, add_to_test_setup = make_setup_registry()


def _add_source_slot(scaffold, name: str, range_: str = "float", unit: str = "cm") -> None:
    """Give ``Person`` a unit-bearing source slot.

    :param scaffold: scaffold to patch
    :param name: slot name to add
    :param range_: LinkML range for the slot
    :param unit: UCUM code declared on the slot
    """
    apply_schema_patch(
        scaffold["source_schema"],
        f"""
    classes:
      Person:
        slots:
          - {name}
    slots:
      {name}:
        range: {range_}
        unit:
          ucum_code: {unit}
""",
    )


def _add_target_slot(scaffold, name: str, range_: str = "float") -> None:
    """Give ``Agent`` a slot to receive a converted value.

    :param scaffold: scaffold to patch
    :param name: slot name to add
    :param range_: LinkML range for the slot
    """
    apply_schema_patch(
        scaffold["target_schema"],
        f"""
    classes:
      Agent:
        slots:
          - {name}
    slots:
      {name}:
        range: {range_}
""",
    )


def _derive(scaffold, target_slot: str, source_slot: str, unit_conversion: str) -> None:
    """Derive *target_slot* from *source_slot* under a ``unit_conversion`` block.

    :param scaffold: scaffold to patch
    :param target_slot: slot being derived
    :param source_slot: slot it is populated from
    :param unit_conversion: YAML body of the ``unit_conversion`` block, indented
    """
    apply_transform_patch(
        scaffold["transform_spec"],
        f"""
    class_derivations:
      Agent:
        slot_derivations:
          {target_slot}:
            populated_from: {source_slot}
            unit_conversion:
{unit_conversion}
""",
    )


@add_to_test_setup
def setup_unit_conversion_bare_magnitude(scaffold):
    """Convert to a bare magnitude when no target slots are named."""
    _add_source_slot(scaffold, "height_cm")
    _add_target_slot(scaffold, "height_m")
    _derive(scaffold, "height_m", "height_cm", "              target_unit: m")
    scaffold["input_data"]["height_cm"] = 120
    scaffold["expected"]["height_m"] = 1.2


@add_to_test_setup
def setup_unit_conversion_structured_value(scaffold):
    """Emit a structured value when target magnitude/unit slots are named."""
    _add_source_slot(scaffold, "depth_cm")
    _add_target_slot(scaffold, "depth_struct", range_="string")
    _derive(
        scaffold,
        "depth_struct",
        "depth_cm",
        "              target_unit: m\n"
        "              target_magnitude_slot: value_converted\n"
        "              target_unit_slot: unit_converted",
    )
    scaffold["input_data"]["depth_cm"] = 250
    scaffold["expected"]["depth_struct"] = {"value_converted": 2.5, "unit_converted": "m"}


@add_to_test_setup
def setup_unit_conversion_numeric_string(scaffold):
    """Convert a numeric value that arrives as a string.

    Tabular sources deliver every column as text, so refusing strings broke
    conversion for TSV input entirely (2fb4f12).
    """
    _add_source_slot(scaffold, "width_cm", range_="string")
    _add_target_slot(scaffold, "width_m")
    _derive(scaffold, "width_m", "width_cm", "              target_unit: m")
    scaffold["input_data"]["width_cm"] = "120"
    scaffold["expected"]["width_m"] = 1.2


@add_to_test_setup
def setup_unit_conversion_none_if_non_numeric(scaffold):
    """Null a non-numeric value when the spec opts in, rather than raising.

    The explicit opt-in for columns mixing coded values with numbers (2fb4f12).
    """
    _add_source_slot(scaffold, "coded_cm", range_="string")
    _add_target_slot(scaffold, "coded_m")
    _derive(
        scaffold,
        "coded_m",
        "coded_cm",
        "              target_unit: m\n              none_if_non_numeric: true",
    )
    scaffold["input_data"]["coded_cm"] = "A"
    scaffold["expected"]["coded_m"] = None


@add_to_test_setup
def setup_unit_conversion_absent_source_value(scaffold):
    """Null a conversion whose source slot is absent from the record."""
    _add_source_slot(scaffold, "missing_cm")
    _add_target_slot(scaffold, "missing_m")
    _derive(scaffold, "missing_m", "missing_cm", "              target_unit: m")
    # deliberately no input_data entry for missing_cm
    scaffold["expected"]["missing_m"] = None


@pytest.mark.parametrize("setup_func", UNIT_CONVERSION_SETUPS, ids=setup_ids(UNIT_CONVERSION_SETUPS))
def test_unit(scaffold, setup_func):
    """Apply one setup, run the transformer, and assert the whole output.

    :param scaffold: fresh scaffold
    :param setup_func: setup under test
    """
    setup_func(scaffold)
    result = run_transformer(scaffold)
    assert result == scaffold["expected"]


# -- error cases: deliberately unregistered, since a raising setup would break
# -- the cumulative integration run for every other feature too.


def test_source_unit_conflicting_with_the_schema_raises(scaffold):
    """A declared ``source_unit`` contradicting the slot's own unit is a spec error.

    Silently trusting either one would convert by the wrong factor.

    :param scaffold: fresh scaffold
    """
    _add_source_slot(scaffold, "height_cm")
    _add_target_slot(scaffold, "height_m")
    _derive(scaffold, "height_m", "height_cm", "              source_unit: mm\n              target_unit: m")
    scaffold["input_data"]["height_cm"] = 100

    with pytest.raises(TransformationError, match="Mismatch in source units") as excinfo:
        run_transformer(scaffold)
    assert isinstance(excinfo.value.cause, ValueError)


def test_non_numeric_string_raises_by_default(scaffold):
    """A non-numeric value is an error unless the spec opts out (2fb4f12).

    Failing loudly is the point: silently nulling would corrupt a column whose
    coded values the curator never intended to convert.

    :param scaffold: fresh scaffold
    """
    _add_source_slot(scaffold, "coded_cm", range_="string")
    _add_target_slot(scaffold, "coded_m")
    _derive(scaffold, "coded_m", "coded_cm", "              target_unit: m")
    scaffold["input_data"]["coded_cm"] = "A"

    with pytest.raises(TransformationError, match="could not convert string to float") as excinfo:
        run_transformer(scaffold)
    assert isinstance(excinfo.value.cause, ValueError)
