"""Completeness of join synthesis across all model locations.

Two guarantees beyond the basic slot-expr case:
1. A spec authored with object_derivations (the deprecated multivalued
   nested-object pattern, flattened into class_derivations at load) still gets
   its cross-table join synthesized.
2. A cross-table reference in a derivation with no enclosing class_derivation
   (top-level enum / permissible-value / slot derivation) fails loud rather than
   silently resolving to None — there is nowhere to host the join.
"""

from __future__ import annotations

import textwrap

import pytest
import yaml

from linkml_map.session import Session

SOURCE = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/completeness
    name: completeness
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: completeness
    default_range: string
    imports: [linkml:types]
    classes:
      Measurement:
        attributes:
          id: {identifier: true}
          subject_id: {range: string}
      Reading:
        attributes:
          id: {identifier: true}
          subject_id: {range: string}
          score: {range: float}
    """)
)


def _transformer(spec_yaml: str):
    session = Session()
    session.set_source_schema(SOURCE)
    session.set_object_transformer(yaml.safe_load(spec_yaml))
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    return tr


#: Derivation sites that cannot host a synthesized join, each spelled two ways:
#: as an expression reference and as a structural dotted ``populated_from``.
UNHOSTABLE_DERIVATIONS = [
    ("enum_derivations:\n  MyEnum:\n    expr: '{Reading.score}'", "enum-expr"),
    (
        "enum_derivations:\n  MyEnum:\n    permissible_value_derivations:\n      PV1:\n        expr: '{Reading.score}'",
        "permissible-value-expr",
    ),
    ("slot_derivations:\n  loose:\n    expr: '{Reading.score}'", "top-level-slot-expr"),
    ("enum_derivations:\n  MyEnum:\n    populated_from: Reading.score", "enum-structural"),
    (
        "enum_derivations:\n  MyEnum:\n    permissible_value_derivations:\n"
        "      PV1:\n        populated_from: Reading.score",
        "permissible-value-structural",
    ),
    ("slot_derivations:\n  loose:\n    populated_from: Reading.score", "top-level-slot-structural"),
]


@pytest.mark.parametrize(
    "derivation_block",
    [pytest.param(block, id=name) for block, name in UNHOSTABLE_DERIVATIONS],
)
def test_cross_table_ref_outside_a_class_derivation_fails_loud(derivation_block):
    """A cross-table reference with nowhere to host a join must fail at normalization.

    Enum derivations, permissible-value derivations and top-level slot derivations
    all sit outside any class_derivation, so there is no block that could carry the
    synthesized ``joins:`` entry. Surfacing that during normalization is the whole
    point — the alternative is silently resolving to None at runtime.

    Both spellings must behave identically: an ``expr`` reference and a structural
    dotted ``populated_from``. The structural half is the counterpart to the #279
    flat-slot fix, where under a class_derivation the join *is* synthesized.

    :param derivation_block: YAML fragment placing the cross-table reference
    """
    tr = _transformer(
        "id: t\ntitle: unhostable cross-table\n"
        "class_derivations:\n"
        "  Result:\n"
        "    populated_from: Measurement\n"
        "    slot_derivations:\n"
        "      id:\n" + derivation_block + "\n"
    )
    with pytest.raises(ValueError, match="cannot be joined"):
        _ = tr.derived_specification


def test_object_derivation_nested_table_synthesizes_join():
    """A spec authored with object_derivations (flattened at load) still gets its join synthesized."""
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: object derivation join
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              readings:
                object_derivations:
                  - class_derivations:
                      Obs:
                        populated_from: Reading
                        slot_derivations:
                          value: {populated_from: score}
        """)
    )
    result_cd = tr.derived_specification.class_derivations[0]
    assert result_cd.joins is not None
    assert "Reading" in result_cd.joins
    assert result_cd.joins["Reading"].join_on == "subject_id"


def test_expr_cross_table_ref_unkeyable_fails_loud():
    """An expr ref to a table with no inferable join key fails loud, not silent None.

    An expression reference has no runtime safety net (it silently resolves to
    None), so an un-keyable one must surface at normalization time.
    """
    source_no_common = yaml.safe_load(
        textwrap.dedent("""\
        id: https://example.org/no-common
        name: no_common
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: no_common
        default_range: string
        imports: [linkml:types]
        classes:
          Measurement:
            attributes:
              id: {identifier: true}
              method: {range: string}
          Reading:
            attributes:
              reading_id: {identifier: true}
              score: {range: float}
        """)
    )
    session = Session()
    session.set_source_schema(source_no_common)
    session.set_object_transformer(
        yaml.safe_load(
            textwrap.dedent("""\
            id: t
            title: expr unkeyable
            class_derivations:
              Result:
                populated_from: Measurement
                slot_derivations:
                  score:
                    expr: '{Reading.score}'
            """)
        )
    )
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    with pytest.raises(ValueError, match="cannot be joined"):
        _ = tr.derived_specification


def test_expr_unknown_qualified_root_fails_loud():
    """A braced ``{Unknown.col}`` whose root is no known table/slot fails at synthesis.

    A same-row slot reference (``{subject_id.x}``) and a bare reference must not.
    """
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: unknown qualified root
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              x:
                expr: '{Nonexistent.col}'
        """)
    )
    with pytest.raises(ValueError, match="cannot be resolved"):
        _ = tr.derived_specification


def test_expr_same_row_qualified_root_is_allowed():
    """A qualified reference rooted in a source slot (same-row/inlined) is not flagged."""
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: same-row qualified root
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              x:
                expr: '{subject_id.upper}'
        """)
    )
    # subject_id is a slot on Measurement → resolvable, no raise.
    assert tr.derived_specification is not None


def test_expr_declared_join_alias_is_allowed():
    """A reference rooted in a declared join alias (alias != schema class) is not flagged.

    Runtime resolves any key in ``class_derivation.joins``; the synthesis guard
    must mirror that and not raise on ``{alias.col}`` for an aliased explicit join.
    """
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: declared join alias
        class_derivations:
          Result:
            populated_from: Measurement
            joins:
              myreading:
                class_named: Reading
                join_on: subject_id
            slot_derivations:
              s:
                expr: '{myreading.score}'
        """)
    )
    # myreading is a declared join alias → resolvable, no raise.
    assert tr.derived_specification is not None


def test_enum_derivation_same_row_reference_is_allowed():
    """A bare (same-row) reference in an enum derivation must not fail — only cross-table does."""
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: enum same-row
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
        enum_derivations:
          MyEnum:
            expr: '{subject_id}'
        """)
    )
    # Computing the derived spec must not raise.
    assert tr.derived_specification is not None


def test_top_level_slot_derivation_fk_path_populated_from_is_allowed():
    """A dotted ``populated_from`` whose root is a slot (not a table) is not flagged.

    Guards the table-vs-slot discrimination: ``subject_id.x`` is an FK/inline path,
    not a cross-table reference, so the unhostable-ref check must leave it alone.
    """
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: top-level slot fk path
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
        slot_derivations:
          loose:
            populated_from: subject_id.x
        """)
    )
    # subject_id is a slot on Measurement, not a source table → not flagged.
    assert tr.derived_specification is not None
