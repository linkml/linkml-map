"""Tests for implicit cross-table join resolution (#212).

When a nested class_derivation has a different populated_from than its parent
and no explicit joins: block, the transformer should:
1. Find common columns between the two source classes
2. Auto-resolve the join on that column
3. Allow slot derivations to reference columns from either table
4. Error on ambiguous columns (present in both) without dot notation
5. Error when no common columns exist
"""

import csv
import textwrap

import pytest
import yaml

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.session import Session
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.errors import TransformationError

SOURCE_SCHEMA = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/implicit-join-test
    name: implicit_join_test
    prefixes:
      linkml: https://w3id.org/linkml/
      xsd: http://www.w3.org/2001/XMLSchema#
    default_prefix: implicit_join_test
    default_range: string
    imports:
      - linkml:types

    classes:
      Measurement:
        attributes:
          id:
            identifier: true
          subject_id:
            range: string
          method:
            range: string

      Reading:
        attributes:
          id:
            identifier: true
          subject_id:
            range: string
          score:
            range: float
""")
)

# Same as above but Reading also has a "method" column (ambiguous with Measurement)
TRANSFORM_SPEC = yaml.safe_load(
    textwrap.dedent("""\
    id: implicit-join-transform
    title: Implicit cross-table join

    class_derivations:
      Result:
        populated_from: Measurement
        slot_derivations:
          id:
          method:
          observation:
            class_derivations:
              - Observation:
                  populated_from: Reading
                  slot_derivations:
                    value:
                      populated_from: score
""")
)

TARGET_SCHEMA_YAML = textwrap.dedent("""\
    id: https://example.org/implicit-join-target
    name: implicit_join_target
    prefixes:
      linkml: https://w3id.org/linkml/
      xsd: http://www.w3.org/2001/XMLSchema#
    default_prefix: implicit_join_target
    default_range: string
    imports:
      - linkml:types

    classes:
      Result:
        attributes:
          id:
            identifier: true
          method:
            range: string
          observation:
            range: Observation
            inlined: true

      Observation:
        attributes:
          value:
            range: float
""")


@pytest.fixture()
def data_dir(tmp_path):
    """Create TSV files for Measurement and Reading tables."""
    measurement_path = tmp_path / "Measurement.tsv"
    with open(measurement_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "M1", "subject_id": "S1", "method": "spirometry"})
        writer.writerow({"id": "M2", "subject_id": "S2", "method": "peak_flow"})

    reading_path = tmp_path / "Reading.tsv"
    with open(reading_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "score"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "R1", "subject_id": "S1", "score": "95.5"})
        writer.writerow({"id": "R2", "subject_id": "S2", "score": "88.0"})

    return tmp_path


@pytest.fixture()
def data_dir_ambiguous(tmp_path):
    """Create TSV files where Reading also has a method column."""
    measurement_path = tmp_path / "Measurement.tsv"
    with open(measurement_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "M1", "subject_id": "S1", "method": "spirometry"})

    reading_path = tmp_path / "Reading.tsv"
    with open(reading_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method", "score"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "R1", "subject_id": "S1", "method": "peak_flow", "score": "95.5"})

    return tmp_path


def _make_transformer(source_schema, transform_spec_dict, target_schema_yaml=None):
    """Create a configured ObjectTransformer."""
    session = Session()
    session.set_source_schema(source_schema)
    session.set_object_transformer(transform_spec_dict)
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    if target_schema_yaml:
        from linkml_runtime import SchemaView

        tr.target_schemaview = SchemaView(target_schema_yaml)
    else:
        tr.target_schemaview = session.target_schemaview
    return tr


@pytest.fixture()
def data_dir_sparse(tmp_path):
    """Create TSV files where one Measurement has no matching Reading (sparse join)."""
    measurement_path = tmp_path / "Measurement.tsv"
    with open(measurement_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "M1", "subject_id": "S1", "method": "spirometry"})
        writer.writerow({"id": "M2", "subject_id": "S_NODATA", "method": "peak_flow"})

    reading_path = tmp_path / "Reading.tsv"
    with open(reading_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "score"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "R1", "subject_id": "S1", "score": "95.5"})

    return tmp_path


@pytest.fixture()
def data_dir_no_match(tmp_path):
    """Create TSV files where no Measurement row has a matching Reading (all sparse)."""
    measurement_path = tmp_path / "Measurement.tsv"
    with open(measurement_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "method"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "M1", "subject_id": "S_NODATA", "method": "spirometry"})

    reading_path = tmp_path / "Reading.tsv"
    with open(reading_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "subject_id", "score"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"id": "R1", "subject_id": "S_OTHER", "score": "95.5"})

    return tmp_path


def test_implicit_join_resolves_via_engine(data_dir):
    """Engine mode: implicit join on common column 'subject_id' resolves nested values."""
    tr = _make_transformer(SOURCE_SCHEMA, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 2

    r1 = results[0]
    assert r1["id"] == "M1"
    assert r1["method"] == "spirometry"
    assert r1["observation"]["value"] == 95.5

    r2 = results[1]
    assert r2["id"] == "M2"
    assert r2["method"] == "peak_flow"
    assert r2["observation"]["value"] == 88.0


def test_implicit_join_ambiguous_columns_resolved_when_one_non_id(data_dir):
    """When both tables share 'id' (identifier) and 'subject_id' (non-id), join on subject_id.

    Ambiguous non-data columns (like 'id') that are identifiers get excluded,
    leaving 'subject_id' as the sole non-id common column.
    """
    tr = _make_transformer(SOURCE_SCHEMA, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 2
    # id columns are ambiguous (both tables have them), but subject_id is the join key
    # The nested row's 'score' should be resolved
    assert results[0]["observation"]["value"] == 95.5
    assert results[1]["observation"]["value"] == 88.0


def test_implicit_join_no_common_columns(data_dir):
    """Error when no common columns exist between parent and nested tables."""
    schema_no_common = yaml.safe_load(
        textwrap.dedent("""\
        id: https://example.org/no-common
        name: no_common
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: no_common
        default_range: string
        imports:
          - linkml:types
        classes:
          Measurement:
            attributes:
              id:
                identifier: true
              method:
                range: string
          Reading:
            attributes:
              reading_id:
                identifier: true
              score:
                range: float
    """)
    )

    tr = _make_transformer(schema_no_common, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    # Diagnostic should specifically call out that no columns are shared,
    # so the user knows whether they need to (a) add a column or (b) pick
    # between candidates.
    with pytest.raises(TransformationError, match="no columns are shared"):
        list(transform_spec(tr, data_loader, source_type="Measurement"))


def test_implicit_join_multiple_non_id_common_columns(data_dir_ambiguous):
    """Error when multiple non-identifier common columns exist (ambiguous join key)."""
    schema_multi_common = yaml.safe_load(
        textwrap.dedent("""\
        id: https://example.org/multi-common
        name: multi_common
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: multi_common
        default_range: string
        imports:
          - linkml:types
        classes:
          Measurement:
            attributes:
              id:
                identifier: true
              subject_id:
                range: string
              method:
                range: string
          Reading:
            attributes:
              id:
                identifier: true
              subject_id:
                range: string
              method:
                range: string
              score:
                range: float
    """)
    )

    tr = _make_transformer(schema_multi_common, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir_ambiguous)

    # Diagnostic should list the candidate columns so the user knows what to
    # disambiguate — not just say "no join could be determined".
    with pytest.raises(TransformationError) as exc:
        list(transform_spec(tr, data_loader, source_type="Measurement"))
    msg = str(exc.value)
    assert "multiple candidate join columns" in msg
    assert "subject_id" in msg
    assert "method" in msg


def test_implicit_join_ambiguous_column_access_errors(data_dir):
    """Accessing a column that exists in both tables without dot notation raises an error."""
    # Both Measurement and Reading have 'id' (identifier) and 'subject_id'.
    # subject_id is the join key, but 'id' is ambiguous in the merged row.
    # A slot derivation that tries to access 'id' should error.
    transform_accessing_ambiguous = yaml.safe_load(
        textwrap.dedent("""\
        id: ambiguous-access-transform
        title: Access ambiguous column

        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          populated_from: id
    """)
    )

    target_with_string_value = textwrap.dedent("""\
        id: https://example.org/target-ambiguous
        name: target_ambiguous
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: target_ambiguous
        default_range: string
        imports:
          - linkml:types
        classes:
          Result:
            attributes:
              id:
                identifier: true
              method:
                range: string
              observation:
                range: Observation
                inlined: true
          Observation:
            attributes:
              value:
                range: string
    """)

    tr = _make_transformer(SOURCE_SCHEMA, transform_accessing_ambiguous, target_with_string_value)
    data_loader = DataLoader(data_dir)

    with pytest.raises(TransformationError, match="ambiguous"):
        list(transform_spec(tr, data_loader, source_type="Measurement"))


def test_implicit_join_continue_on_error(data_dir):
    """Errors from implicit joins are collectible via on_error callback."""
    schema_no_common = yaml.safe_load(
        textwrap.dedent("""\
        id: https://example.org/no-common-coe
        name: no_common_coe
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: no_common_coe
        default_range: string
        imports:
          - linkml:types
        classes:
          Measurement:
            attributes:
              id:
                identifier: true
              method:
                range: string
          Reading:
            attributes:
              reading_id:
                identifier: true
              score:
                range: float
    """)
    )

    tr = _make_transformer(schema_no_common, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    errors: list[TransformationError] = []
    results = list(transform_spec(tr, data_loader, source_type="Measurement", on_error=errors.append))

    # Should collect errors instead of raising
    assert len(errors) == 2  # one per Measurement row
    assert all("no implicit join could be synthesized" in str(e) for e in errors)
    # Results should still be produced (with whatever the error handler allows)
    assert len(results) == 0  # rows that errored are skipped


def test_implicit_join_expr_simple_field(data_dir):
    """Expr {score} resolves from nested table via merged row."""
    transform_with_expr = yaml.safe_load(
        textwrap.dedent("""\
        id: expr-simple-transform
        title: Expr with simple field from nested table

        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          expr: '{score}'
    """)
    )

    tr = _make_transformer(SOURCE_SCHEMA, transform_with_expr, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 2
    assert results[0]["observation"]["value"] == 95.5
    assert results[1]["observation"]["value"] == 88.0


def test_implicit_join_expr_dot_notation(data_dir):
    """Expr {Reading.score} resolves via implicit join lookup."""
    transform_with_dot_expr = yaml.safe_load(
        textwrap.dedent("""\
        id: expr-dot-transform
        title: Expr with dot notation for implicit join

        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          expr: '{Reading.score}'
    """)
    )

    tr = _make_transformer(SOURCE_SCHEMA, transform_with_dot_expr, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 2
    assert results[0]["observation"]["value"] == 95.5
    assert results[1]["observation"]["value"] == 88.0


def test_implicit_join_expr_ambiguous_column_errors(data_dir):
    """Expr {id} errors when id is ambiguous between parent and nested tables."""
    transform_ambiguous_expr = yaml.safe_load(
        textwrap.dedent("""\
        id: expr-ambiguous-transform
        title: Expr accessing ambiguous column

        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          expr: '{id}'
    """)
    )

    target_string_value = textwrap.dedent("""\
        id: https://example.org/target-expr-ambig
        name: target_expr_ambig
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: target_expr_ambig
        default_range: string
        imports:
          - linkml:types
        classes:
          Result:
            attributes:
              id:
                identifier: true
              method:
                range: string
              observation:
                range: Observation
                inlined: true
          Observation:
            attributes:
              value:
                range: string
    """)

    tr = _make_transformer(SOURCE_SCHEMA, transform_ambiguous_expr, target_string_value)
    data_loader = DataLoader(data_dir)

    with pytest.raises(TransformationError, match="ambiguous"):
        list(transform_spec(tr, data_loader, source_type="Measurement"))


# --- Dot-notation disambiguation tests ---

TARGET_STRING_OBS = textwrap.dedent("""\
    id: https://example.org/target-disambig
    name: target_disambig
    prefixes:
      linkml: https://w3id.org/linkml/
      xsd: http://www.w3.org/2001/XMLSchema#
    default_prefix: target_disambig
    default_range: string
    imports:
      - linkml:types
    classes:
      Result:
        attributes:
          id:
            identifier: true
          method:
            range: string
          observation:
            range: Observation
            inlined: true
      Observation:
        attributes:
          value:
            range: string
""")


def test_populated_from_dot_notation_disambiguates_nested(data_dir):
    """populated_from: Reading.id resolves to the nested table's id."""
    transform = yaml.safe_load(
        textwrap.dedent("""\
        id: disambig-nested
        title: test
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          populated_from: Reading.id
    """)
    )

    tr = _make_transformer(SOURCE_SCHEMA, transform, TARGET_STRING_OBS)
    data_loader = DataLoader(data_dir)
    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert results[0]["observation"]["value"] == "R1"
    assert results[1]["observation"]["value"] == "R2"


def test_populated_from_dot_notation_disambiguates_parent(data_dir):
    """populated_from: Measurement.id resolves to the parent table's id."""
    transform = yaml.safe_load(
        textwrap.dedent("""\
        id: disambig-parent
        title: test
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          populated_from: Measurement.id
    """)
    )

    tr = _make_transformer(SOURCE_SCHEMA, transform, TARGET_STRING_OBS)
    data_loader = DataLoader(data_dir)
    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert results[0]["observation"]["value"] == "M1"
    assert results[1]["observation"]["value"] == "M2"


def test_expr_dot_notation_disambiguates_both_tables(data_dir):
    """Expr can use dot notation to access either table's ambiguous columns."""
    transform = yaml.safe_load(
        textwrap.dedent("""\
        id: disambig-expr
        title: test
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          expr: '{Reading.id} + "_" + {Measurement.id}'
    """)
    )

    tr = _make_transformer(SOURCE_SCHEMA, transform, TARGET_STRING_OBS)
    data_loader = DataLoader(data_dir)
    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert results[0]["observation"]["value"] == "R1_M1"
    assert results[1]["observation"]["value"] == "R2_M2"


def test_implicit_join_sparse_data_no_match(data_dir_sparse):
    """When a join key has no match in the secondary table, the nested object is absent.

    This is the sparse-data case: subject S_NODATA exists in Measurement but not
    in Reading. The parent row is still produced, but the nested object — which is
    anchored to ``populated_from: Reading`` — is ``None`` rather than a hollow
    ``{value: None}``. That keeps "no Reading row exists" distinguishable from
    "a Reading row exists but score is null" (#217 bug 1, re: #211). No error is
    raised — this is expected for optional/sparse joins, distinct from "no join
    could be determined" (which is a spec-level error).
    """
    tr = _make_transformer(SOURCE_SCHEMA, TRANSFORM_SPEC, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir_sparse)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 2

    # S1 has a matching Reading — resolved normally
    assert results[0]["id"] == "M1"
    assert results[0]["observation"]["value"] == 95.5

    # S_NODATA has no matching Reading — no nested object emitted, no error
    assert results[1]["id"] == "M2"
    assert results[1]["observation"] is None


def test_sparse_no_match_does_not_silently_resolve_ambiguous_to_parent(data_dir_no_match):
    """A join miss must not silently resolve ambiguous columns to the parent row.

    Regression for #217 bug 2 (data-dependent ambiguity enforcement). Previously
    the no-match path passed the bare parent row to ``map_object``, so an ambiguous
    column like ``id`` silently resolved to the parent's value — while a matching
    row would *raise* on the same access. Enforcement was therefore data-dependent.
    Now no object is emitted on a miss, so the result is ``None`` and the parent's
    ``id`` ("M1") never leaks through as the nested value.
    """
    transform_accessing_ambiguous = yaml.safe_load(
        textwrap.dedent("""\
        id: ambiguous-access-transform
        title: Access ambiguous column
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          populated_from: id
    """)
    )
    target_with_string_value = textwrap.dedent("""\
        id: https://example.org/target-ambiguous
        name: target_ambiguous
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: target_ambiguous
        default_range: string
        imports:
          - linkml:types
        classes:
          Result:
            attributes:
              id:
                identifier: true
              method:
                range: string
              observation:
                range: Observation
                inlined: true
          Observation:
            attributes:
              value:
                range: string
    """)

    tr = _make_transformer(SOURCE_SCHEMA, transform_accessing_ambiguous, target_with_string_value)
    data_loader = DataLoader(data_dir_no_match)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 1
    # No matching Reading → no object, and crucially not the parent's id ("M1").
    assert results[0]["observation"] is None


def test_implicit_join_dot_notation_miss_yields_none(data_dir_no_match):
    """A nested value read via dot notation yields no object when the join misses (#217)."""
    transform_dot = yaml.safe_load(
        textwrap.dedent("""\
        id: dot-miss-transform
        title: Dot notation on join miss
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          populated_from: Reading.score
    """)
    )

    tr = _make_transformer(SOURCE_SCHEMA, transform_dot, TARGET_SCHEMA_YAML)
    data_loader = DataLoader(data_dir_no_match)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 1
    assert results[0]["observation"] is None


def test_implicit_join_multivalued_all_miss_yields_empty_list(data_dir_no_match):
    """A multivalued nested slot whose joins all miss yields [] rather than [None] (#217).

    This is the blood-pressure-style case: a set of nested observations where none
    of the underlying readings exist. The parent is still emitted, but its nested
    collection is empty rather than a list of hollow objects.
    """
    transform_multi = yaml.safe_load(
        textwrap.dedent("""\
        id: multi-miss-transform
        title: Multivalued nested all-miss
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              observations:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value:
                          populated_from: score
    """)
    )
    target_multivalued = textwrap.dedent("""\
        id: https://example.org/target-multi
        name: target_multi
        prefixes:
          linkml: https://w3id.org/linkml/
          xsd: http://www.w3.org/2001/XMLSchema#
        default_prefix: target_multi
        default_range: string
        imports:
          - linkml:types
        classes:
          Result:
            attributes:
              id:
                identifier: true
              observations:
                range: Observation
                multivalued: true
                inlined_as_list: true
          Observation:
            attributes:
              value:
                range: float
    """)

    tr = _make_transformer(SOURCE_SCHEMA, transform_multi, target_multivalued)
    data_loader = DataLoader(data_dir_no_match)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert len(results) == 1
    assert results[0]["observations"] == []


def test_ambiguous_sentinel_survives_deepcopy_and_pickle():
    """The _AMBIGUOUS sentinel must remain identity-equal after deepcopy and pickle.

    Identity is checked via ``is _AMBIGUOUS`` everywhere it's used. If the
    sentinel doesn't survive copy/pickle, a copied or pickled MergedRow
    would silently lose ambiguity detection and let the sentinel slip through
    as a real value.
    """
    import copy
    import pickle

    from linkml_map.transformer.object_transformer import _AMBIGUOUS, _AmbiguousType

    assert copy.deepcopy(_AMBIGUOUS) is _AMBIGUOUS
    assert copy.copy(_AMBIGUOUS) is _AMBIGUOUS
    assert pickle.loads(pickle.dumps(_AMBIGUOUS)) is _AMBIGUOUS
    # Constructing a new instance returns the same singleton.
    assert _AmbiguousType() is _AMBIGUOUS


TARGET_FLAT_SCORE = textwrap.dedent("""\
    id: https://example.org/target-flat-score
    name: target_flat_score
    prefixes:
      linkml: https://w3id.org/linkml/
      xsd: http://www.w3.org/2001/XMLSchema#
    default_prefix: target_flat_score
    default_range: string
    imports:
      - linkml:types
    classes:
      Result:
        attributes:
          id:
            identifier: true
          method:
            range: string
          score:
            range: float
""")

FLAT_DOT_TRANSFORM = yaml.safe_load(
    textwrap.dedent("""\
    id: flat-dotted-transform
    title: Flat top-level dotted populated_from
    class_derivations:
      Result:
        populated_from: Measurement
        slot_derivations:
          id:
          method:
          score:
            populated_from: Reading.score
""")
)


def test_flat_dot_notation_normalization_synthesizes_join():
    """A flat top-level ``populated_from: Reading.score`` must not crash normalization (#279).

    Regression: ``induce_missing_values`` treated the whole ``Reading.score`` string as
    a bare slot on the primary class ``Measurement`` and raised during normalization,
    before any runtime path was reached. The implicit-join synthesizer must also cover
    flat top-level slots (not just nested class_derivations), so accessing
    ``derived_specification`` both succeeds and adds the join.
    """
    tr = _make_transformer(SOURCE_SCHEMA, FLAT_DOT_TRANSFORM, TARGET_FLAT_SCORE)

    derived = tr.derived_specification

    result_cd = derived.class_derivations[0]
    assert result_cd.joins is not None
    assert "Reading" in result_cd.joins
    assert result_cd.joins["Reading"].join_on == "subject_id"


def test_flat_dot_notation_resolves_via_engine(data_dir):
    """Flat top-level ``populated_from: Reading.score`` resolves via the synthesized join (#279).

    The issue's minimal repro has no ``joins:`` block; the join is auto-synthesized on
    the shared ``subject_id`` column, and the joined table's ``score`` lands on the
    flat top-level target slot.
    """
    tr = _make_transformer(SOURCE_SCHEMA, FLAT_DOT_TRANSFORM, TARGET_FLAT_SCORE)
    data_loader = DataLoader(data_dir)

    results = list(transform_spec(tr, data_loader, source_type="Measurement"))

    assert results[0]["score"] == 95.5
    assert results[1]["score"] == 88.0
