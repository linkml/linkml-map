"""The set-based join engine must produce identical output to the per-row path.

Covers the real dbGaP shapes: flat expr joins, nested objects, arbitrary depth,
sparse misses (#217), and multivalued nesting via multiple class_derivations.
"""

from __future__ import annotations

import csv
import logging
import textwrap

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.session import Session
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.join_engine import _collect_joins, can_use_join_engine


def _write(tmp_path, tables: dict[str, tuple[list[str], list[list]]]) -> None:
    for name, (cols, rows) in tables.items():
        with open(tmp_path / f"{name}.tsv", "w", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(cols)
            w.writerows(rows)


def _transformer(source_schema: dict, spec: dict, target_schema: str):
    session = Session()
    session.set_source_schema(source_schema)
    session.set_object_transformer(spec)
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    tr.target_schemaview = SchemaView(target_schema)
    return tr


def _run(tmp_path, source_schema, spec, target_schema, source_type, tables):
    """Run the spec through ``transform_spec`` (production dispatch) and return sorted output.

    ``transform_spec`` routes these subject-keyed specs through the join engine (its
    default when the block is engine-capable), so this exercises the real production
    path. Parity against the per-row lookup path is covered by the pre-existing join
    suites, which run their human-validated expected outputs through the same dispatch.
    """
    _write(tmp_path, tables)
    tr = _transformer(source_schema, spec, target_schema)
    out = list(transform_spec(tr, DataLoader(tmp_path, schemaview=tr.source_schemaview), source_type=source_type))

    def key(r):
        return r.get("id") or r.get("set_id") or str(r)

    return sorted(out, key=key)


SRC = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/je
    name: je
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: je
    default_range: string
    imports: [linkml:types]
    classes:
      Measurement: {attributes: {id: {identifier: true}, subject_id: {range: string}, method: {range: string}}}
      Reading: {attributes: {subject_id: {identifier: true}, score: {range: float}, visit: {range: integer}}}
      Other: {attributes: {subject_id: {identifier: true}, label: {range: string}}}
    """)
)

MEAS = ("Measurement", (["id", "subject_id", "method"], [["M1", "S1", "spiro"], ["M2", "S2", "peak"]]))
READING = ("Reading", (["subject_id", "score", "visit"], [["S1", "95.5", "1"], ["S2", "88.0", "2"]]))


def test_flat_expr_join(tmp_path):
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, method: {range: string}, reading_score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: flat
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              reading_score: {expr: '{Reading.score}'}
    """)
    )
    out = _run(tmp_path, SRC, spec, target, "Measurement", dict([MEAS, READING]))
    assert out[0]["reading_score"] == 95.5


def test_nested_object(tmp_path):
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, observation: {range: Observation, inlined: true}}}
          Observation: {attributes: {value: {range: float}, visit_num: {range: integer}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: nested
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations:
                        value: {populated_from: score}
                        visit_num: {populated_from: visit}
    """)
    )
    out = _run(tmp_path, SRC, spec, target, "Measurement", dict([MEAS, READING]))
    assert out[0]["observation"] == {"value": 95.5, "visit_num": 1}


def test_sparse_miss_suppresses_object(tmp_path):
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, observation: {range: Observation, inlined: true}}}
          Observation: {attributes: {value: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: sparse
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              observation:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations: {value: {populated_from: score}}
    """)
    )
    # S_GONE has no Reading row -> nested object suppressed (None)
    meas = ("Measurement", (["id", "subject_id", "method"], [["M1", "S1", "x"], ["M2", "S_GONE", "y"]]))
    out = _run(tmp_path, SRC, spec, target, "Measurement", dict([meas, READING]))
    miss = next(r for r in out if r["id"] == "M2")
    assert miss["observation"] is None


@pytest.mark.parametrize(
    "reading_content",
    ["", "subject_id\tscore\tvisit\n"],
    ids=["zero_byte", "header_only"],
)
def test_empty_joined_file_degrades_to_null(tmp_path, reading_content):
    """A 0-byte/headerless joined file must degrade to null, not crash the block (#276 regression)."""
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, method: {range: string}, reading_score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: empty-join
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              reading_score: {expr: '{Reading.score}'}
    """)
    )
    _write(tmp_path, dict([MEAS]))
    (tmp_path / "Reading.tsv").write_text(reading_content)  # 0-byte or header-only
    tr = _transformer(SRC, spec, target)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    out = list(transform_spec(tr, dl, source_type="Measurement"))
    assert len(out) == 2  # every primary row survives
    assert all(r.get("reading_score") is None for r in out)  # join degraded to null, no crash


def test_primary_missing_source_key_degrades_to_null(tmp_path, caplog):
    """A primary file that shares the model but omits the join key column must not crash.

    Study-arm/cohort files sometimes drop a column the schema declares. ``can_use_join_engine``
    gates on the *schema* (which has the column), so the block reaches the engine; the file
    probe must then degrade the join to null and log, exactly as a missing joined-side key does,
    rather than binding ``m."subject_id"`` and aborting the block with a BinderException.
    """
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, method: {range: string}, reading_score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: missing-source-key
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              method:
              reading_score: {expr: '{Reading.score}'}
    """)
    )
    # Measurement file omits subject_id (the source_key) though the schema declares it.
    measurements = ("Measurement", (["id", "method"], [["M1", "spiro"], ["M2", "peak"]]))
    _write(tmp_path, dict([measurements, READING]))
    tr = _transformer(SRC, spec, target)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    with caplog.at_level(logging.WARNING):
        out = list(transform_spec(tr, dl, source_type="Measurement"))
    assert len(out) == 2  # every primary row survives
    assert all(r.get("reading_score") is None for r in out)  # join degraded to null, no crash
    assert any("Reading" in r.message and "subject_id" in r.message for r in caplog.records)  # misfire logged


def test_all_engine_run_creates_no_lookup_index(tmp_path):
    """An all-engine-capable spec must not open a LookupIndex — the per-row fallback's
    in-memory DuckDB connection is pure overhead when the engine handles every block.
    """
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, reading_score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: t
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              reading_score: {expr: '{Reading.score}'}
    """)
    )
    _write(tmp_path, dict([MEAS, READING]))
    tr = _transformer(SRC, spec, target)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    # Observe mid-run (before the generator's cleanup detaches the index): with eager
    # creation the index exists here; lazily it stays None because the engine handled
    # the block. Post-run state can't distinguish the two — the finally detaches either way.
    gen = transform_spec(tr, dl, source_type="Measurement")
    first = next(gen)
    assert first["reading_score"] == 95.5  # engine actually ran
    assert tr.lookup_index is None  # no LookupIndex opened for an all-engine block
    assert len(list(gen)) == 1  # exhaust the remaining row so the generator runs its cleanup


def test_multivalued_via_multiple_class_derivations(tmp_path):
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result:
            attributes:
              id: {identifier: true}
              observations: {range: Observation, multivalued: true, inlined_as_list: true}
          Observation: {attributes: {value: {range: string}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: multivalued
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              observations:
                class_derivations:
                  - Observation:
                      populated_from: Reading
                      slot_derivations: {value: {populated_from: score}}
                  - Observation:
                      populated_from: Other
                      slot_derivations: {value: {populated_from: label}}
    """)
    )
    other = ("Other", (["subject_id", "label"], [["S1", "a"], ["S2", "b"]]))
    out = _run(tmp_path, SRC, spec, target, "Measurement", dict([MEAS, READING, other]))
    assert len(out[0]["observations"]) == 2


# --- dispatch capability + to-many dedup ---

FK_SRC = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/fk
    name: fk
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: fk
    default_range: string
    imports: [linkml:types]
    classes:
      Measurement:
        attributes:
          id: {identifier: true}
          subject_id: {range: string}
          org: {range: Org}
      Org: {attributes: {org_id: {identifier: true}, name: {range: string}}}
      Reading: {attributes: {subject_id: {identifier: true}, score: {range: float}}}
    """)
)

TARGET_VAL = textwrap.dedent("""\
    id: https://example.org/t
    name: t
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: t
    default_range: string
    imports: [linkml:types]
    classes:
      Result: {attributes: {id: {identifier: true}, value: {range: string}}}
""")


def _cd(source_schema, spec):
    session = Session()
    session.set_source_schema(source_schema)
    session.set_object_transformer(spec)
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    return tr


def test_simple_subject_join_is_engine_capable(tmp_path):
    _write(tmp_path, dict([MEAS, READING]))
    spec = yaml.safe_load(
        "id: t\ntitle: t\nclass_derivations:\n  Result:\n    populated_from: Measurement\n"
        "    slot_derivations:\n      id:\n      value: {expr: '{Reading.score}'}\n"
    )
    tr = _cd(FK_SRC, spec)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    cd = tr.derived_specification.class_derivations[0]
    assert can_use_join_engine(cd, dl, tr.source_schemaview) is True


def test_fk_chain_is_not_engine_capable(tmp_path):
    """A dotted populated_from to a non-joined table (FK chain) must fall back to per-row."""
    _write(tmp_path, dict([MEAS, READING]))
    spec = yaml.safe_load(
        "id: t\ntitle: t\nclass_derivations:\n  Result:\n    populated_from: Measurement\n"
        "    slot_derivations:\n      id:\n      value: {populated_from: org.name}\n"
    )
    tr = _cd(FK_SRC, spec)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    cd = tr.derived_specification.class_derivations[0]
    assert can_use_join_engine(cd, dl, tr.source_schemaview) is False


def test_join_missing_lookup_key_is_not_engine_capable(tmp_path):
    """A join resolving a source_key but no lookup_key/join_on must fail the gate, not crash later.

    ``can_use_join_engine`` is a non-raising capability probe. If it ignored ``lookup_key``,
    such a join would pass the gate and then raise in ``_build_join_sql`` via ``join_keys`` —
    turning a capability decision into a runtime exception mid-dispatch.
    """
    _write(tmp_path, dict([MEAS, READING]))
    spec = yaml.safe_load(
        "id: t\ntitle: t\nclass_derivations:\n  Result:\n    populated_from: Measurement\n"
        "    slot_derivations:\n      id:\n      value: {expr: '{Reading.score}'}\n"
    )
    tr = _cd(FK_SRC, spec)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    cd = tr.derived_specification.class_derivations[0]
    # Force a join with a source_key but no lookup_key (nor join_on).
    join = cd.joins["Reading"]
    join.source_key, join.lookup_key, join.join_on = "subject_id", None, None
    assert can_use_join_engine(cd, dl, tr.source_schemaview) is False


def test_conflicting_join_name_across_nesting_raises():
    """The same join name resolving to different keys at different nesting levels is a
    spec contradiction — a flattened star join can't make one name mean two joins — and
    the per-row path (_collect_all_joins) already raises on it. The engine must too,
    rather than silently keeping the first via setdefault.
    """
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: t
        class_derivations:
          Result:
            populated_from: Measurement
            joins:
              Reading: {join_on: subject_id}
            slot_derivations:
              id:
              reading_score: {expr: '{Reading.score}'}
              nested:
                class_derivations:
                  - Observation:
                      populated_from: Measurement
                      joins:
                        Reading: {source_key: method, lookup_key: visit}
                      slot_derivations:
                        v: {expr: '{Reading.visit}'}
        """)
    )
    cd = _cd(SRC, spec).derived_specification.class_derivations[0]
    with pytest.raises(ValueError, match=r"Conflicting join specs for 'Reading'"):
        _collect_joins(cd, {})


def test_distinct_join_names_to_same_table_do_not_conflict():
    """Joining a table two ways is spelled with distinct join names, which coexist.

    Guards that the conflict check keys on the join *name*, not the table: two names
    pointing at the same class with different keys is the legitimate multi-join pattern.
    """
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: t
        class_derivations:
          Result:
            populated_from: Measurement
            joins:
              by_subject: {class_named: Reading, source_key: subject_id, lookup_key: subject_id}
              by_method: {class_named: Reading, source_key: method, lookup_key: subject_id}
            slot_derivations:
              id:
        """)
    )
    cd = _cd(SRC, spec).derived_specification.class_derivations[0]
    joins = _collect_joins(cd, {})  # must not raise
    assert {"by_subject", "by_method"} <= set(joins)


def test_to_many_join_does_not_explode_rows(tmp_path):
    """A to-many join table must not duplicate primary rows (deduped to one per key)."""
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, reading_score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: t
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              reading_score: {expr: '{Reading.score}'}
    """)
    )
    # Two Reading rows for S1 (to-many on the key)
    reading_many = ("Reading", (["subject_id", "score", "visit"], [["S1", "95.5", "1"], ["S1", "10.0", "2"]]))
    measurements = ("Measurement", (["id", "subject_id", "method"], [["M1", "S1", "x"]]))
    out = _run(tmp_path, SRC, spec, target, "Measurement", dict([measurements, reading_many]))
    # Exactly one output row per Measurement — no cartesian explosion.
    assert len(out) == 1


def test_repeated_primary_keys_are_not_collapsed_by_join(tmp_path):
    """Distinct primary rows sharing a join key must all survive (no dedup on the primary).

    Regression guard: a to-many *join* is deduped to one row per key, but the
    *primary* must not be — 3 subjects x 3 measurements = 9 primary rows joined
    to a subject-keyed table must yield 9 outputs, not 3 (the streaming collapse
    reverted in 5806939 keyed dedup on the subject id and dropped 6).
    """
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, reading_score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: t
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              reading_score: {expr: '{Reading.score}'}
    """)
    )
    # 3 subjects x 3 distinct measurements = 9 primary rows sharing subject keys.
    meas_rows = [[f"{s}-{m}", s, m] for s in ("S1", "S2", "S3") for m in ("a", "b", "c")]
    measurements = ("Measurement", (["id", "subject_id", "method"], meas_rows))
    reading = ("Reading", (["subject_id", "score", "visit"], [[s, "9.9", "1"] for s in ("S1", "S2", "S3")]))
    out = _run(tmp_path, SRC, spec, target, "Measurement", dict([measurements, reading]))
    assert len(out) == 9  # every distinct primary row survives, not collapsed to one per subject


def test_yaml_backed_table_is_not_engine_capable(tmp_path):
    """A YAML-backed table can't be read by the DuckDB join, so the block falls back to per-row."""
    _write(tmp_path, dict([MEAS]))  # Measurement as TSV
    (tmp_path / "Reading.yaml").write_text("- subject_id: S1\n  score: 95.5\n  visit: 1\n")
    spec = yaml.safe_load(
        "id: t\ntitle: t\nclass_derivations:\n  Result:\n    populated_from: Measurement\n"
        "    slot_derivations:\n      id:\n      value: {expr: '{Reading.score}'}\n"
    )
    tr = _cd(SRC, spec)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    cd = tr.derived_specification.class_derivations[0]
    assert can_use_join_engine(cd, dl, tr.source_schemaview) is False


def test_missing_or_non_class_primary_is_not_engine_capable(tmp_path):
    """No source schema, or a primary that isn't a source class, must fall back (not crash)."""
    _write(tmp_path, dict([MEAS, READING]))
    spec = yaml.safe_load(
        "id: t\ntitle: t\nclass_derivations:\n  Result:\n    populated_from: Measurement\n"
        "    slot_derivations:\n      id:\n      value: {expr: '{Reading.score}'}\n"
    )
    tr = _cd(FK_SRC, spec)
    dl = DataLoader(tmp_path, schemaview=tr.source_schemaview)
    cd = tr.derived_specification.class_derivations[0]
    # No schema at all -> conservative False, not an AttributeError on None.
    assert can_use_join_engine(cd, dl, None) is False
    # A schema that doesn't contain the primary class -> conservative False.
    other_sv = SchemaView(
        textwrap.dedent("""\
        id: https://example.org/other
        name: other
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: other
        default_range: string
        imports: [linkml:types]
        classes:
          Reading: {attributes: {subject_id: {identifier: true}, score: {range: float}}}
    """)
    )
    assert can_use_join_engine(cd, dl, other_sv) is False


def test_primary_column_named_like_join_alias_is_preserved(tmp_path):
    """A real primary column sharing a joined table's name must survive, not be dropped as a struct."""
    source = yaml.safe_load(
        textwrap.dedent("""\
        id: https://example.org/collide
        name: collide
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: collide
        default_range: string
        imports: [linkml:types]
        classes:
          Measurement:
            attributes:
              id: {identifier: true}
              subject_id: {range: string}
              Reading: {range: string}
          Reading: {attributes: {subject_id: {identifier: true}, score: {range: float}}}
    """)
    )
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, tag: {range: string}, score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: t
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              tag: {populated_from: Reading}
              score: {expr: '{Reading.score}'}
    """)
    )
    meas = ("Measurement", (["id", "subject_id", "Reading"], [["M1", "S1", "hello"]]))
    reading = ("Reading", (["subject_id", "score"], [["S1", "95.5"]]))
    out = _run(tmp_path, source, spec, target, "Measurement", dict([meas, reading]))
    assert out[0]["tag"] == "hello"  # primary column preserved despite the name collision
    assert out[0]["score"] == 95.5  # joined table's column still resolved


def test_join_resolves_when_alias_differs_from_join_key(tmp_path):
    """The engine keys MergedRow by the ``joins`` dict key, not ``join.alias``.

    ``alias`` is the ``key: true`` slot, so it normally equals the joins key, but it
    can diverge under programmatic construction. ``_resolve_joined_row`` always looks
    up ``rows_by_table`` by the joins key, so keying the merge by ``alias`` would put
    the row under a key the runtime never reads, silently breaking the join.
    """
    target = textwrap.dedent("""\
        id: https://example.org/t
        name: t
        prefixes: {linkml: https://w3id.org/linkml/}
        default_prefix: t
        default_range: string
        imports: [linkml:types]
        classes:
          Result: {attributes: {id: {identifier: true}, reading_score: {range: float}}}
    """)
    spec = yaml.safe_load(
        textwrap.dedent("""\
        id: t
        title: t
        class_derivations:
          Result:
            populated_from: Measurement
            slot_derivations:
              id:
              reading_score: {expr: '{Reading.score}'}
    """)
    )
    _write(tmp_path, dict([MEAS, READING]))
    tr = _transformer(SRC, spec, target)
    cd = tr.derived_specification.class_derivations[0]
    # Force alias != joins key ("Reading"); the runtime resolves by the key.
    cd.joins["Reading"].alias = "aliased_reading"
    out = sorted(
        transform_spec(tr, DataLoader(tmp_path, schemaview=tr.source_schemaview), source_type="Measurement"),
        key=lambda r: r["id"],
    )
    assert out[0]["reading_score"] == 95.5
