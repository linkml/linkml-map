"""Tests for join-key inference."""

from __future__ import annotations

import textwrap

from linkml_runtime import SchemaView

from linkml_map.utils.join_utils import infer_join_key, pick_join_key


def test_prefers_subject_key_over_other_common_columns():
    """dbGaP_Subject_ID wins even when another common column exists (which pick_join_key can't pick)."""
    sv = SchemaView(
        textwrap.dedent("""\
        id: x
        name: x
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: x
        default_range: string
        imports: [linkml:types]
        classes:
          A:
            attributes:
              a_id: {identifier: true}
              dbGaP_Subject_ID: {range: string}
              site: {range: string}
          B:
            attributes:
              b_id: {identifier: true}
              dbGaP_Subject_ID: {range: string}
              site: {range: string}
        """)
    )
    # pick_join_key is ambiguous (two non-id common cols) -> None
    assert pick_join_key(sv, "A", "B") is None
    # inference prefers the subject key
    assert infer_join_key(sv, "A", "B") == "dbGaP_Subject_ID"


def test_falls_back_to_pick_join_key_without_subject_key():
    sv = SchemaView(
        textwrap.dedent("""\
        id: x
        name: x
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: x
        default_range: string
        imports: [linkml:types]
        classes:
          A:
            attributes:
              a_id: {identifier: true}
              subject_id: {range: string}
          B:
            attributes:
              b_id: {identifier: true}
              subject_id: {range: string}
        """)
    )
    assert infer_join_key(sv, "A", "B") == "subject_id"


def test_returns_none_when_no_common_column():
    sv = SchemaView(
        textwrap.dedent("""\
        id: x
        name: x
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: x
        default_range: string
        imports: [linkml:types]
        classes:
          A:
            attributes:
              a_id: {identifier: true}
          B:
            attributes:
              b_id: {identifier: true}
        """)
    )
    assert infer_join_key(sv, "A", "B") is None
