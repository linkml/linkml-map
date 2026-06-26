"""End-to-end tests for lazy join materialization, sparse-miss logging, and fail-fast.

These exercise the streaming engine path: joined tables register on first use and
accumulate only referenced columns; sparse misses are summarized at INFO; and a join
referencing a missing data file fails hard rather than silently producing no matches.
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
from linkml_map.transformer.errors import TransformationError
from linkml_map.utils.lookup_index import LookupIndex

SOURCE_SCHEMA = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/lazy-join-test
    name: lazy_join_test
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: lazy_join_test
    default_range: string
    imports: [linkml:types]
    classes:
      Measurement:
        attributes:
          id: {identifier: true}
          subject_id: {range: string}
          method: {range: string}
      Reading:
        attributes:
          id: {identifier: true}
          subject_id: {range: string}
          score: {range: float}
    """)
)

TRANSFORM_SPEC = yaml.safe_load(
    textwrap.dedent("""\
    id: lazy-join-transform
    title: Lazy join
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

TARGET_SCHEMA = textwrap.dedent("""\
    id: https://example.org/lazy-join-target
    name: lazy_join_target
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: lazy_join_target
    default_range: string
    imports: [linkml:types]
    classes:
      Result:
        attributes:
          id: {identifier: true}
          method: {range: string}
          observation: {range: Observation, inlined: true}
      Observation:
        attributes:
          value: {range: float}
""")


def _make_transformer():
    session = Session()
    session.set_source_schema(SOURCE_SCHEMA)
    session.set_object_transformer(TRANSFORM_SPEC)
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    return tr


def _write_measurement(path, subjects):
    with open(path / "Measurement.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["id", "subject_id", "method"])
        for i, s in enumerate(subjects):
            w.writerow([f"M{i}", s, "spirometry"])


def _write_wide_reading(path, subjects, n_extra=200):
    cols = ["id", "subject_id", "score", *[f"extra{j}" for j in range(n_extra)]]
    with open(path / "Reading.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(cols)
        for i, s in enumerate(subjects):
            w.writerow([f"R{i}", s, 95.5, *[f"v{i}_{j}" for j in range(n_extra)]])


def test_wide_join_table_materializes_only_referenced_columns(tmp_path):
    """A wide joined table loads only the key + the one referenced column."""
    subjects = [f"S{i}" for i in range(10)]
    _write_measurement(tmp_path, subjects)
    _write_wide_reading(tmp_path, subjects, n_extra=200)

    tr = _make_transformer()
    idx = LookupIndex()
    tr.lookup_index = idx  # pre-attach to inspect after the run
    loader = DataLoader(tmp_path, schemaview=tr.source_schemaview)

    results = list(transform_spec(tr, loader, source_type="Measurement"))

    assert results[0]["observation"]["value"] == 95.5
    assert len(idx.header("Reading")) == 203  # id, subject_id, score, extra0..199
    assert idx._tables["Reading"].materialized == {"subject_id", "score"}
    idx.close()


def test_sparse_miss_logs_info_summary(tmp_path, caplog):
    """End-of-block summary reports the count of source rows with no matching join row."""
    _write_measurement(tmp_path, ["S0", "S1", "S_NOPE", "S_ALSO_NOPE"])
    _write_wide_reading(tmp_path, ["S0", "S1"], n_extra=3)

    tr = _make_transformer()
    loader = DataLoader(tmp_path, schemaview=tr.source_schemaview)

    with caplog.at_level(logging.INFO, logger="linkml_map.transformer.engine"):
        results = list(transform_spec(tr, loader, source_type="Measurement"))

    assert len(results) == 4
    summaries = [r.message for r in caplog.records if "had no matching row" in r.message]
    assert len(summaries) == 1
    assert "2 of 4" in summaries[0]
    assert "Reading" in summaries[0]


def test_absent_join_file_fails_hard(tmp_path):
    """A join that references a table with no data file fails fast at first use."""
    _write_measurement(tmp_path, ["S0", "S1"])
    # Deliberately do NOT write Reading.tsv

    tr = _make_transformer()
    loader = DataLoader(tmp_path, schemaview=tr.source_schemaview)

    with pytest.raises(TransformationError, match="No data file found"):
        list(transform_spec(tr, loader, source_type="Measurement"))
