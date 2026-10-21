"""Resolve the spellings a spec uses for an enum value to the enum's permissible value keys."""

from collections.abc import Callable
from dataclasses import dataclass

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model.meta import EnumDefinition

_DYNAMIC_ENUM_SLOTS = ("reachable_from", "matches", "concepts", "include", "minus", "inherits")


@dataclass(frozen=True)
class EnumIndex:
    """Lookup from each spelling of an enum's permissible values to their keys.

    Spellings are matched in tiers: the key, then ``meaning`` (compared as expanded
    URIs), then ``title``, then ``aliases``. The first tier with any match decides,
    so a value that is already a key always resolves to itself, even when another
    permissible value uses it as a title.
    """

    enum_name: str
    tiers: tuple[dict[str, frozenset[str]], ...]
    expand: Callable[[str], str]

    @classmethod
    def from_enum(cls, enum: EnumDefinition, expand: Callable[[str], str]) -> "EnumIndex":
        """Build the index for *enum*.

        :param enum: The enum definition.
        :param expand: Expands a CURIE to a URI, returning anything else unchanged.
        :return: The index.
        """
        tiers: tuple[dict[str, set[str]], ...] = ({}, {}, {}, {})
        for key, pv in enum.permissible_values.items():
            tiers[0].setdefault(key, set()).add(key)
            if pv.meaning:
                tiers[1].setdefault(expand(pv.meaning), set()).add(key)
            if pv.title:
                tiers[2].setdefault(pv.title, set()).add(key)
            for alias in pv.aliases or []:
                tiers[3].setdefault(alias, set()).add(key)
        return cls(
            enum.name,
            tuple({s: frozenset(keys) for s, keys in tier.items()} for tier in tiers),
            expand,
        )

    def match(self, value: str) -> frozenset[str]:
        """Return the keys *value* resolves to.

        >>> from linkml_runtime.linkml_model.meta import EnumDefinition
        >>> enum = EnumDefinition(
        ...     "SexEnum",
        ...     permissible_values={
        ...         "OMOP:8532": {"title": "FEMALE", "meaning": "OMOP:8532"},
        ...         "OMOP:8507": {"title": "MALE", "meaning": "OMOP:8507"},
        ...         "MALE": {"title": "male (legacy)"},
        ...     },
        ... )
        >>> index = EnumIndex.from_enum(enum, expand=lambda c: c)
        >>> sorted(index.match("FEMALE"))
        ['OMOP:8532']
        >>> sorted(index.match("MALE"))
        ['MALE']
        >>> sorted(index.match("unknown"))
        []

        :param value: A spelling from the spec or the data.
        :return: The matching keys from the first tier with any match; empty when
            nothing matches, more than one when the value is ambiguous in that tier.
        """
        for tier, spelling in zip(self.tiers, (value, self.expand(value), value, value), strict=True):
            if spelling in tier:
                return tier[spelling]
        return frozenset()

    def resolve(self, value: str) -> tuple[str | None, str | None]:
        """Return the key *value* resolves to, or why it doesn't resolve to exactly one.

        >>> from linkml_runtime.linkml_model.meta import EnumDefinition
        >>> enum = EnumDefinition("Color", permissible_values={"R": {"title": "red"}, "r": {"title": "red"}})
        >>> index = EnumIndex.from_enum(enum, expand=lambda c: c)
        >>> index.resolve("R")
        ('R', None)
        >>> index.resolve("red")
        (None, "'red' matches more than one permissible value of enum Color: ['R', 'r']")
        >>> index.resolve("blue")
        (None, "'blue' is not a permissible value of enum Color")

        :param value: A spelling from the spec or the data.
        :return: ``(key, None)`` on a unique match, else ``(None, problem)``.
        """
        keys = self.match(value)
        if len(keys) == 1:
            return next(iter(keys)), None
        if keys:
            return None, f"{value!r} matches more than one permissible value of enum {self.enum_name}: {sorted(keys)}"
        return None, f"{value!r} is not a permissible value of enum {self.enum_name}"


def enum_index(sv: SchemaView, enum_name: str) -> EnumIndex | None:
    """Build the index for a schema's enum, or ``None`` if its values aren't all listed.

    Enums defined partly or wholly by a query or by other enums (``reachable_from``,
    ``inherits`` and the like) have no closed list of permissible values to resolve
    against, so their values pass through unchanged.

    :param sv: The schema containing the enum.
    :param enum_name: Name of the enum.
    :return: The index, or ``None``.
    """
    enum = sv.get_enum(enum_name)
    if not enum.permissible_values or any(getattr(enum, s) for s in _DYNAMIC_ENUM_SLOTS):
        return None
    return EnumIndex.from_enum(enum, sv.expand_curie)
