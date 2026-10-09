"""JSON and YAML serialization that keeps ``decimal`` values exact.

Neither the standard library's ``json`` nor PyYAML's default dumper can write a
:class:`~decimal.Decimal` as a number: ``json`` raises and PyYAML emits a
Python-specific tag.  Converting to ``float`` would silently round, so every
serialization of transformed data goes through these helpers instead.
"""

from decimal import Decimal
from typing import Any

import simplejson
import yaml


def format_decimal(value: Decimal) -> str:
    """Render a decimal in fixed-point notation, preserving every digit.

    ``str(Decimal)`` switches to exponent notation for small values, which YAML
    would read back as a string and which reads poorly in tabular output.

    >>> format_decimal(Decimal("52.30"))
    '52.30'
    >>> format_decimal(Decimal("1E-7"))
    '0.0000001'
    >>> format_decimal(Decimal("1E+3"))
    '1000'
    """
    return format(value, "f")


def dumps_json(obj: Any, **kwargs: Any) -> str:
    """Serialize *obj* as JSON, writing decimals as exact numeric literals.

    Keyword arguments are passed to :func:`simplejson.dumps`.

    >>> dumps_json({"v": Decimal("0.123456789012345678901")})
    '{"v": 0.123456789012345678901}'
    """
    kwargs.setdefault("ensure_ascii", False)
    # Matches the standard library's default, which simplejson 4 flipped.
    kwargs.setdefault("allow_nan", True)
    return simplejson.dumps(obj, use_decimal=True, **kwargs)


class _DecimalDumper(yaml.Dumper):
    """PyYAML's default dumper, plus a plain-scalar representation for decimals."""


def _represent_decimal(dumper: yaml.Dumper, value: Decimal) -> yaml.ScalarNode:
    """Represent a decimal as a plain int or float scalar with all its digits."""
    text = format_decimal(value)
    tag = "tag:yaml.org,2002:float" if "." in text else "tag:yaml.org,2002:int"
    return dumper.represent_scalar(tag, text)


_DecimalDumper.add_representer(Decimal, _represent_decimal)


def dump_yaml(obj: Any, **kwargs: Any) -> str:
    """Serialize *obj* as YAML, writing decimals as exact plain scalars.

    Keyword arguments are passed to :func:`yaml.dump`.

    >>> dump_yaml({"v": Decimal("52.30"), "n": Decimal("52")})
    'n: 52\\nv: 52.30\\n'
    """
    kwargs.setdefault("default_flow_style", False)
    kwargs.setdefault("allow_unicode", True)
    return yaml.dump(obj, Dumper=_DecimalDumper, **kwargs)
