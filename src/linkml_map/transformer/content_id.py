"""Identifiers synthesized from the content of a derived record (#342).

When a target class has an identifier slot and the spec derives none, the record's
id is a UUID5 hash of the record itself::

    id = uuid5(f"{target schema id}/{TargetClass}", canonical(record))

The same harmonized record always gets the same id, and different records get
different ids, independent of row order, chunking, or parallel execution.  These
are content hashes, not stable identifiers: any change to a derived value changes
the id.  Minting is opt-in with ``mint_ids: true`` on the specification, a target
class's entry in ``class_defaults``, or a class derivation (see :func:`mints_ids`), and
an explicit derivation of the identifier slot always wins.  An identifier that is
neither derived nor minted is an error: the transformer refuses to emit records
without it.

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
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from json.encoder import encode_basestring
from typing import Any

from linkml_runtime import SchemaView


def mints_ids(spec_mint_ids: bool | None, default_mint_ids: bool | None, class_mint_ids: bool | None) -> bool:
    """Whether a class derivation mints ids.

    The first setting given wins: the derivation's own, then its target class's entry in
    ``class_defaults``, then the specification's; with none given, minting is off.

    >>> mints_ids(None, None, None), mints_ids(True, None, None)
    (False, True)
    >>> mints_ids(False, True, None), mints_ids(False, True, False)
    (True, False)
    """
    for setting in (class_mint_ids, default_mint_ids, spec_mint_ids):
        if setting is not None:
            return setting
    return False


def missing_identifier_message(class_name: str, id_slot: str) -> str:
    """Explain an identifier slot that a class derivation neither derives nor mints."""
    return (
        f"Class derivation {class_name!r} does not derive identifier slot {id_slot!r} and mint_ids is not true; "
        "derive it explicitly or set mint_ids: true"
    )


def canonical_json(value: Any) -> str:
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
    if isinstance(value, str):
        # What json.dumps(value, ensure_ascii=False) does for a string, minus its overhead.
        return encode_basestring(value)
    return json.dumps(value)


@dataclass
class ContentIdSynthesizer:
    """Synthesizes content-hash identifiers for records of one target schema."""

    schemaview: SchemaView
    """The target schema; its ``id`` is the base of every namespace."""

    _identifier_slots: dict[str, str | None] = field(default_factory=dict, repr=False)
    _slot_descriptions: dict[str, dict[str, tuple[bool, str | None]]] = field(default_factory=dict, repr=False)
    _namespaces: dict[str, uuid.UUID] = field(default_factory=dict, repr=False)

    def identifier_slot(self, class_name: str) -> str | None:
        """The identifier slot of *class_name*, if records of it need one.

        ``None`` if the class has no identifier, isn't in the schema, or is abstract or
        a mixin (it never has instances of its own).
        """
        if class_name not in self._identifier_slots:
            slot = None
            cls = self.schemaview.all_classes().get(class_name)
            if cls is not None and not cls.abstract and not cls.mixin:
                slot = self.schemaview.get_identifier_slot(class_name)
            self._identifier_slots[class_name] = slot.name if slot else None
        return self._identifier_slots[class_name]

    def content_id(self, record: dict[str, Any], class_name: str) -> str:
        """Hash *record*, an instance of target class *class_name*, into a UUID5 string."""
        if class_name not in self._namespaces:
            # Same two-level scheme as the uuid5() expression function.
            self._namespaces[class_name] = uuid.uuid5(uuid.NAMESPACE_URL, f"{self.schemaview.schema.id}/{class_name}")
        return str(
            uuid.uuid5(self._namespaces[class_name], _encode(_canonical(record, False, self._describe, class_name)))
        )

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
