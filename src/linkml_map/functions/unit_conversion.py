"""
Basic unit conversion functions.

Currently only native pint units or UCUM units are supported.

For UCUM, the ucumvert library is used to convert UCUM units to pint units,
see `<https://github.com/dalito/ucumvert>`_.
"""

from enum import Enum
from functools import lru_cache
from typing import Any, Optional, Union

import lark
import pint
from ucumvert import PintUcumRegistry


class UnitSystem(str, Enum):
    """Enumeration of supported unit systems."""

    UCUM = "ucum"
    IEC61360 = "iec61360"
    SI = "SI"


REGISTRIES = {
    UnitSystem.UCUM: PintUcumRegistry(),
}


class UndefinedUnitError(Exception):
    """
    Raised when a unit is not defined.

    Note: equivalent to the pint error, but the
    pint dependency is optional
    """


class QuantitySyntaxError(Exception):
    """
    Raised when a quantity cannot be parsed.
    """


class DimensionalityError(Exception):
    """
    Raised when a unit conversion cannot be performed.

    Note: equivalent to the pint error, but the
    pint dependency is optional
    """


def convert_units(
    magnitude: float, from_unit: str, to_unit: str, system: Optional[UnitSystem] = None
) -> Any:
    """
    Convert a quantity between units.

    >>> convert_units(1, "m", "cm")
    100.0
    >>> convert_units(1, "m", "cm", system=UnitSystem.UCUM)
    100.0
    >>> convert_units(1, "m", "cm", system=UnitSystem.SI)
    100.0
    >>> convert_units(1.0, "hectare", "m^2", system=UnitSystem.SI)
    10000.0
    >>> convert_units(1.0, "hectare", "m ** 2", system=UnitSystem.SI)
    10000.0
    >>> convert_units(1.0, "hectare", "m ** 2", system=None)
    10000.0
    >>> convert_units(1.0, "km2", "m2", system=UnitSystem.UCUM)
    1000000.0

    :param magnitude:
    :param from_unit:
    :param to_unit:
    :return: converted magnitude
    """
    ureg: pint.UnitRegistry = get_unit_registry(system)
    from_unit = normalize_unit(from_unit, system)
    to_unit = normalize_unit(to_unit, system)
    try:
        from_unit_q = ureg.parse_units(from_unit)
    except lark.exceptions.UnexpectedCharacters as err:
        msg = f"Cannot parse unit: {from_unit}"
        raise UndefinedUnitError(msg) from err
    except pint.errors.UndefinedUnitError as err:
        msg = f"Unknown source unit: {from_unit}"
        raise UndefinedUnitError(msg) from err
    quantity = magnitude * from_unit_q
    try:
        return quantity.to(to_unit).magnitude
    except pint.errors.UndefinedUnitError as err:
        msg = f"Unknown target unit: {from_unit}"
        raise UndefinedUnitError(msg) from err
    except pint.errors.DimensionalityError as err:
        msg = f"Cannot convert from {from_unit} to {to_unit}"
        raise DimensionalityError(msg) from err


@lru_cache
def get_unit_registry(
    system: Optional[UnitSystem] = None,
) -> Union[pint.UnitRegistry, PintUcumRegistry]:
    """
    Get a unit registry.

    >>> ureg = get_unit_registry(UnitSystem.UCUM)
    >>> ureg.from_ucum("m/s2.kg")
    <Quantity(1.0, 'meter * kilogram / second ** 2')>
    >>> str(_)
    '1.0 kilogram * meter / second ** 2'
    >>> ureg.from_ucum("m[H2O]{35Cel}")  # UCUM code with annotation
    <Quantity(1, 'm_H2O')>
    >>> _.to("mbar")
    <Quantity(98.0665, 'millibar')>
    >>> ureg("degC")   # a standard pint unit
    <Quantity(1, 'degree_Celsius')>
    >>> ureg.from_ucum("g/m2")
    <Quantity(1.0, 'gram / meter ** 2')>
    >>> _.to(ureg.from_ucum("kg/m2"))
    <Quantity(0.001, 'kilogram / meter ** 2')>
    >>> ureg.from_ucum("nmol/mmol{Cre}")
    <Quantity(1.0, 'nanomole / millimole')>
    >>> sireg = get_unit_registry(UnitSystem.SI)
    >>> sireg("degC")
    <Quantity(1, 'degree_Celsius')>
    >>> sireg("ha")
    <Quantity(1, 'hectare')>

    :param system: currently only supported values are None or UnitSystem.UCUM
    :return:
    """
    import pint

    ureg = pint.UnitRegistry()
    if not system:
        return ureg
    if system in REGISTRIES:
        return REGISTRIES[system]
    if system.value in dir(ureg.sys):
        ureg.default_system = system.value
        return ureg
    msg = f"Unknown unit system: {system}"
    raise NotImplementedError(msg)


def normalize_unit(unit: str, system: Optional[UnitSystem] = None) -> str:
    """Normalize the unit to UnitSystem.UCUM, if possible."""
    if system is None or system != UnitSystem.UCUM:
        return unit

    # this is UnitSystem.UCUM
    try:
        return str(get_unit_registry(system).from_ucum(unit))
    except pint.errors.UndefinedUnitError as err:
        msg = f"Unknown unit: {unit}"
        raise UndefinedUnitError(msg) from err
    except lark.exceptions.UnexpectedCharacters as err:
        msg = f"Cannot parse unit: {unit}"
        raise UndefinedUnitError(msg) from err
