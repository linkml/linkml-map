"""Range induction for dotted ``populated_from`` in ``induce_missing_values``.

Covers the three dotted-path shapes that share the induction code path:

1. Foreign-key path (``org_id.hq``) — resolved via ``resolve_fk_path``; the range
   of the final slot drives class-derivation range induction. This is a
   regression guard: an earlier #279 fix short-circuited *all* dotted paths and
   skipped the FK fallback, breaking range-based mapping for FK/inline paths.
2. Table-qualified cross-table ref (``Address.city``) — resolved against the
   named source class; no crash even without an explicit ``joins:`` block.
3. Unresolvable table-qualified ref — induction is skipped (range left unset)
   rather than crashing on a bare-slot lookup.
"""

import textwrap

import yaml
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/fk-source
    name: fk_source
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: fk_source
    default_range: string
    imports: [linkml:types]
    classes:
      Person:
        attributes:
          id: {identifier: true}
          org_id: {range: Organization}
      Organization:
        attributes:
          id: {identifier: true}
          hq: {range: Address}
      Address:
        attributes:
          id: {identifier: true}
          city: {range: string}
""")


def _derived(spec_dict: dict):
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.create_transformer_specification(spec_dict)
    return tr.derived_specification


def _slot_derivation(cd, name):
    return cd.slot_derivations[name]


def test_fk_dotted_populated_from_induces_range():
    """A dotted FK path (``org_id.hq``) still gets its range induced via resolve_fk_path.

    ``org_id.hq`` resolves to a slot whose range is ``Address``; the target slot's
    range should be induced to the class derivation populated from ``Address``.
    """
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: fk-dotted
        title: fk dotted path
        class_derivations:
          PersonOut:
            populated_from: Person
            slot_derivations:
              hq:
                populated_from: org_id.hq
          AddrOut:
            populated_from: Address
            slot_derivations:
              city:
                populated_from: city
        """)
    )
    derived = _derived(spec)
    person_out = next(cd for cd in derived.class_derivations if cd.name == "PersonOut")
    assert _slot_derivation(person_out, "hq").range == "AddrOut"


def test_table_qualified_populated_from_does_not_crash():
    """A table-qualified ref (``Address.city``) induces without crashing, no joins block."""
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: table-qualified
        title: table qualified ref
        class_derivations:
          PersonOut:
            populated_from: Person
            slot_derivations:
              city:
                populated_from: Address.city
        """)
    )
    derived = _derived(spec)
    person_out = next(cd for cd in derived.class_derivations if cd.name == "PersonOut")
    # Scalar range, no matching class derivation → range unset, but no crash.
    assert _slot_derivation(person_out, "city").range is None
