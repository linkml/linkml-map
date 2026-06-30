"""The set-based join engine must produce identical output to the per-row path.

Covers the real dbGaP shapes: flat expr joins, nested objects, arbitrary depth,
sparse misses (#217), and multivalued nesting via multiple class_derivations.
"""

from __future__ import annotations

import csv
import textwrap

import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.session import Session
from linkml_map.transformer.engine import transform_spec
from linkml_map.transformer.join_engine import can_use_join_engine, transform_via_join


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


def _both(tmp_path, source_schema, spec, target_schema, source_type, tables):
    """Return (per_row, engine) outputs, each sorted, for the same inputs."""
    _write(tmp_path, tables)
    tr1 = _transformer(source_schema, spec, target_schema)
    per_row = list(transform_spec(tr1, DataLoader(tmp_path, schemaview=tr1.source_schemaview), source_type=source_type))
    tr2 = _transformer(source_schema, spec, target_schema)
    engine = list(
        transform_via_join(tr2, DataLoader(tmp_path, schemaview=tr2.source_schemaview), source_type=source_type)
    )

    def key(r):
        return r.get("id") or r.get("set_id") or str(r)

    return sorted(per_row, key=key), sorted(engine, key=key)


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
    per_row, engine = _both(tmp_path, SRC, spec, target, "Measurement", dict([MEAS, READING]))
    assert per_row == engine
    assert engine[0]["reading_score"] == 95.5


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
    per_row, engine = _both(tmp_path, SRC, spec, target, "Measurement", dict([MEAS, READING]))
    assert per_row == engine
    assert engine[0]["observation"] == {"value": 95.5, "visit_num": 1}


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
    # S_GONE has no Reading row -> nested object suppressed (None) in both paths
    meas = ("Measurement", (["id", "subject_id", "method"], [["M1", "S1", "x"], ["M2", "S_GONE", "y"]]))
    per_row, engine = _both(tmp_path, SRC, spec, target, "Measurement", dict([meas, READING]))
    assert per_row == engine
    miss = next(r for r in engine if r["id"] == "M2")
    assert miss["observation"] is None


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
    per_row, engine = _both(tmp_path, SRC, spec, target, "Measurement", dict([MEAS, READING, other]))
    assert per_row == engine
    assert len(engine[0]["observations"]) == 2


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
    _, engine = _both(tmp_path, SRC, spec, target, "Measurement", dict([measurements, reading_many]))
    # Exactly one output row per Measurement — no cartesian explosion.
    assert len(engine) == 1


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
