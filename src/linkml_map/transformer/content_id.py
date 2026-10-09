"""Identifiers synthesized from the content of a derived record (#342).

When a target class has an identifier slot and the spec derives none, the record's
id is a UUID5 hash of the record itself::

    id = uuid5(f"{target schema id}/{TargetClass}", canonical(record))

The same harmonized record always gets the same id, and different records get
different ids, independent of row order, chunking, or parallel execution.  These
are content hashes, not stable identifiers: any change to a derived value changes
the id.  An explicit derivation of the identifier slot always wins.

The canonical form is a contract — changing it changes every synthesized id:

- objects: keys sorted; entries whose value is null, an empty list, or an empty
  object are dropped
- lists: items canonicalized and sorted by their encoding, unless the target slot
  declares ``list_elements_ordered``
- numbers: ints, floats, and decimals share one format — fixed-point, no trailing
  zeros, no exponent, ``-0`` as ``0``; floats are first rounded to 15 significant
  digits so unit-conversion noise doesn't split a record
- booleans and strings: JSON literals; strings escaped as ``json.dumps`` does with
  ``ensure_ascii=False``
- whitespace: none
"""

import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from linkml_runtime import SchemaView

from linkml_map.utils.eval_utils import _uuid5


def canonical_json(value: Any, slot_order: dict[str, tuple[bool, str | None]] | None = None) -> str:
    """Encode *value* in the canonical form, ignoring any schema-declared list order.

    >>> canonical_json({"b": 5.0, "a": None, "c": [], "d": ["y", "x"]})
    '{"b":5,"d":["x","y"]}'
    >>> canonical_json([Decimal("52.30"), 52.3, 155.44800000000001, -0.0, 1e-7, 100])
    '[0,0.0000001,100,155.448,52.3,52.3]'

    The list above is sorted by each item's encoding, as text.
    """
    return _encode(_canonical(value, ordered=False, describe=lambda _: {}))


def _canonical(value: Any, ordered: bool, describe: Any, class_name: str | None = None) -> Any:
    """Reduce *value* to its canonical structure.

    :param value: A derived value.
    :param ordered: Whether a list here keeps its order.
    :param describe: Maps a class name to ``{slot: (ordered, range class)}``.
    :param class_name: The target class *value* instantiates, if it is an object.
    :return: Nested dicts, lists, strings, booleans, and normalized decimals.
    :raises TypeError: For a value with no canonical form.
    """
    if isinstance(value, dict):
        slots = describe(class_name) if class_name else {}
        out = {}
        for key, item in value.items():
            item_ordered, item_class = slots.get(key, (False, None))
            canonical = _canonical(item, item_ordered, describe, item_class)
            if not _is_absent(canonical):
                out[key] = canonical
        return out
    if isinstance(value, list):
        items = [c for c in (_canonical(item, False, describe, class_name) for item in value) if not _is_absent(c)]
        return items if ordered else sorted(items, key=_encode)
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int | float | Decimal):
        return _canonical_number(value)
    msg = f"Cannot synthesize an identifier from a value of type {type(value).__name__}: {value!r}"
    raise TypeError(msg)


def _canonical_number(value: int | float | Decimal) -> Decimal:
    """Normalize a number so equal values compare and encode identically.

    >>> [str(_canonical_number(v)) for v in (5, 5.0, Decimal("5.00"))]
    ['5', '5', '5']
    >>> str(_canonical_number(-0.0))
    '0'
    """
    number = Decimal(format(value, ".15g")) if isinstance(value, float) else Decimal(value)
    if number.is_zero():
        return Decimal(0)
    return number.normalize()


def _is_absent(value: Any) -> bool:
    """Whether a canonical value counts as missing: null, ``[]``, or ``{}``."""
    return value is None or (isinstance(value, dict | list) and not value)


def _encode(value: Any) -> str:
    """Serialize a canonical structure; see the module docstring for the format."""
    if isinstance(value, dict):
        return "{" + ",".join(f"{_encode(k)}:{_encode(v)}" for k, v in sorted(value.items())) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_encode(v) for v in value) + "]"
    if isinstance(value, Decimal):
        return format(value, "f")
    return json.dumps(value, ensure_ascii=False)


@dataclass
class ContentIdSynthesizer:
    """Synthesizes content-hash identifiers for records of one target schema."""

    schemaview: SchemaView
    """The target schema; its ``id`` is the base of every namespace."""

    _identifier_slots: dict[str, str | None] = field(default_factory=dict, repr=False)
    _slot_descriptions: dict[str, dict[str, tuple[bool, str | None]]] = field(default_factory=dict, repr=False)

    def identifier_slot(self, class_name: str) -> str | None:
        """The identifier slot of *class_name*, or ``None`` if it has none or isn't in the schema."""
        if class_name not in self._identifier_slots:
            slot = None
            if class_name in self.schemaview.all_classes():
                slot = self.schemaview.get_identifier_slot(class_name)
            self._identifier_slots[class_name] = slot.name if slot else None
        return self._identifier_slots[class_name]

    def content_id(self, record: dict[str, Any], class_name: str) -> str:
        """Hash *record*, an instance of target class *class_name*, into a UUID5 string."""
        namespace = f"{self.schemaview.schema.id}/{class_name}"
        return _uuid5(namespace, _encode(_canonical(record, False, self._describe, class_name)))

    def _describe(self, class_name: str) -> dict[str, tuple[bool, str | None]]:
        """``{slot: (list_elements_ordered, range class or None)}`` for *class_name*, cached."""
        if class_name not in self._slot_descriptions:
            description = {}
            if class_name in self.schemaview.all_classes():
                classes = self.schemaview.all_classes()
                for slot in self.schemaview.class_induced_slots(class_name):
                    range_class = slot.range if slot.range in classes else None
                    description[slot.name] = (bool(slot.list_elements_ordered), range_class)
            self._slot_descriptions[class_name] = description
        return self._slot_descriptions[class_name]
