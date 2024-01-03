"""
Basic unit conversion functions.

Currently uses pint, which is an optional dependency. But
note that pint may not work well with UCUM, see:

- https://github.com/hgrecco/pint/issues/1769
"""
import re
from enum import Enum
from functools import lru_cache
from typing import Any, Optional


class UnitSystem(str, Enum):
    UCUM = "ucum"
    IEC61360 = "iec61360"
    SI = "si"


# TODO: this is currently highly incomplete; consider deriving from established mappings
MAPPINGS = {
    UnitSystem.UCUM: {
        "mo": "month",
        "Cel": "degC",
    },
}


class UndefinedUnitError(Exception):
    """
    Raised when a unit is not defined.

    Note: equivalent to the pint error, but the
    pint dependency is optional
    """


class DimensionalityError(Exception):
    """
    Raised when a unit conversion cannot be performed.

    Note: equivalent to the pint error, but the
    pint dependency is optional
    """


def convert_units(
    magnitude: float, from_unit: str, to_unit: str, system: Optional[UnitSystem] = None
):
    """
    Convert a quantity between units.

    :param magnitude:
    :param from_unit:
    :param to_unit:
    :return:
    """
    import pint

    ureg: pint.UnitRegistry = get_unit_registry(system)
    from_unit = normalize_unit(from_unit, system)
    to_unit = normalize_unit(to_unit, system)
    try:
        from_unit_q = ureg.parse_units(from_unit)
    except pint.errors.UndefinedUnitError:
        raise UndefinedUnitError(f"Unknown source unit: {from_unit}")
    quantity = magnitude * from_unit_q
    try:
        return quantity.to(to_unit).magnitude
    except pint.errors.UndefinedUnitError:
        raise UndefinedUnitError(f"Unknown target unit: {from_unit}")
    except pint.errors.DimensionalityError:
        raise DimensionalityError(f"Cannot convert from {from_unit} to {to_unit}")


@lru_cache()
def get_unit_registry(system: Optional[UnitSystem] = None) -> Any:
    """
    Get a unit registry.

    :param system:
    :return:
    """
    import pint

    ureg = pint.UnitRegistry()
    if not system:
        return ureg
    if system not in MAPPINGS:
        raise NotImplementedError(f"Unknown unit system: {system}")
    for k, v in MAPPINGS[system].items():
        ureg.define(f"{k} = {v}")
    return ureg


def normalize_unit(unit: str, system: Optional[UnitSystem] = None) -> str:
    if system is None:
        return unit
    if system == UnitSystem.UCUM:
        return remove_ucum_annotations(convert_to_exponential_format(convert_dot_to_slash(unit)))
    else:
        return unit


def remove_ucum_annotations(code: str) -> str:
    """
    Remove UCUM annotations from text.

    >>> remove_ucum_annotations("nmol/mmol{Cre}")
    'nmol/mmol'

    :param text:
    :return:
    """
    # Regular expression to find and replace UCUM annotations
    return re.sub(r"\{.*?\}", "", code)


def convert_to_exponential_format(code: str) -> str:
    """
    Convert units like g/m2 to g/m^2 in the given text.

    >>> convert_to_exponential_format("g/m2")
    'g/m^2'

    """
    # Regular expression to find and replace units like g/m2 to g/m^2
    return re.sub(r"(\w+)/(\w+)(\d+)", r"\1/\2^\3", code)


def convert_dot_to_slash(text):
    """
    Convert units from forms like pmol.umol-1 to pmol/umol in the given text.

    >>> convert_dot_to_slash("pmol.umol-1")
    'pmol/umol'
    """
    # Regular expression to find and replace units like pmol.umol-1 to pmol/umol
    return re.sub(r"(\w+)\.(\w+)-1", r"\1/\2", text)
