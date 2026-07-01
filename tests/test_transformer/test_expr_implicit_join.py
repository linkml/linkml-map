"""Implicit joins synthesized from expression references.

A `{Table.col}` reference inside an `expr:` (with no `joins:` block and no nested
class_derivation for that table) must synthesize the join — previously it was
invisible to synthesis and silently resolved to None. This is the dominant real
pattern (bdc-harmonized-variables: 440 specs, zero `joins:` blocks).
"""

from __future__ import annotations

import csv
import textwrap

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.session import Session
from linkml_map.transformer.engine import transform_spec

SOURCE = yaml.safe_load(
    textwrap.dedent("""\
    id: https://example.org/expr-implicit
    name: expr_implicit
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: expr_implicit
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

TARGET = textwrap.dedent("""\
    id: https://example.org/expr-implicit-target
    name: expr_implicit_target
    prefixes: {linkml: https://w3id.org/linkml/}
    default_prefix: expr_implicit_target
    default_range: string
    imports: [linkml:types]
    classes:
      Result:
        attributes:
          id: {identifier: true}
          method: {range: string}
          reading_score: {range: float}
""")

# Result pulls a flat slot via expr {Reading.score} — NO joins: block, NO nested CD.
SPEC = yaml.safe_load(
    textwrap.dedent("""\
    id: expr-implicit-transform
    title: expr implicit join, no joins block
    class_derivations:
      Result:
        populated_from: Measurement
        slot_derivations:
          id:
          method:
          reading_score:
            expr: '{Reading.score}'
    """)
)


@pytest.fixture()
def data_dir(tmp_path):
    with open(tmp_path / "Measurement.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["id", "subject_id", "method"])
        w.writerow(["M1", "S1", "spiro"])
    with open(tmp_path / "Reading.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["id", "subject_id", "score"])
        w.writerow(["R1", "S1", "95.5"])
    return tmp_path


def _transformer():
    session = Session()
    session.set_source_schema(SOURCE)
    session.set_object_transformer(SPEC)
    tr = session.object_transformer
    tr.source_schemaview = session.source_schemaview
    tr.target_schemaview = SchemaView(TARGET)
    return tr


def test_expr_reference_synthesizes_join():
    """The normalizer synthesizes a join for the table referenced only in the expr."""
    tr = _transformer()
    result_cd = tr.derived_specification.class_derivations[0]
    assert result_cd.joins is not None
    assert "Reading" in result_cd.joins
    assert result_cd.joins["Reading"].join_on == "subject_id"


def test_expr_implicit_join_resolves_value(data_dir):
    """End to end: {Reading.score} resolves instead of silently returning None."""
    tr = _transformer()
    loader = DataLoader(data_dir, schemaview=tr.source_schemaview)
    results = list(transform_spec(tr, loader, source_type="Measurement"))
    assert len(results) == 1
    assert results[0]["reading_score"] == 95.5  # previously None
