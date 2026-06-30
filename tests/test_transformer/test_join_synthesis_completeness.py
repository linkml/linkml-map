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


def test_enum_derivation_cross_table_ref_fails_loud():
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: enum cross-table
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
        enum_derivations:
          MyEnum:
            expr: '{Reading.score}'
        """)
    )
    with pytest.raises(ValueError, match="cannot be joined"):
        _ = tr.derived_specification


def test_permissible_value_derivation_cross_table_ref_fails_loud():
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: pv cross-table
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
        enum_derivations:
          MyEnum:
            permissible_value_derivations:
              PV1:
                expr: '{Reading.score}'
        """)
    )
    with pytest.raises(ValueError, match="cannot be joined"):
        _ = tr.derived_specification


def test_top_level_slot_derivation_cross_table_ref_fails_loud():
    tr = _transformer(
        textwrap.dedent("""\
        id: t
        title: top-level slot cross-table
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
        slot_derivations:
          loose:
            expr: '{Reading.score}'
        """)
    )
    with pytest.raises(ValueError, match="cannot be joined"):
        _ = tr.derived_specification


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
