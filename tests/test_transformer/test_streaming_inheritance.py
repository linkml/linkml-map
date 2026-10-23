"""Streamed tabular input applies is_a inheritance between class derivations, as single objects do (#358)."""

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map import ObjectTransformer
from linkml_map.loaders.data_loaders import DataLoader
from linkml_map.transformer.engine import transform_spec

SOURCE = """\
id: https://example.org/s
name: s
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string
classes:
  samples:
    attributes:
      sample_id:
        identifier: true
      site:
  sites:
    attributes:
      site_code:
        identifier: true
      site_name:
"""

BASE = {"slot_derivations": {"tag": {"expr": "'from-base'"}}}
CHILD_SLOTS = {"sample_id": None, "site": {"expr": "{sites.site_name}"}}
# The key columns are named differently, so the join can't be synthesized from a shared column.
JOIN = {"sites": {"source_key": "site", "lookup_key": "site_code"}}


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "samples.tsv").write_text("sample_id\tsite\nS1\tA\nS2\tB\n")
    (tmp_path / "sites.tsv").write_text("site_code\tsite_name\nA\tAlpha\nB\tBeta\n")
    return tmp_path


def _stream(spec: dict, data_dir) -> list[dict]:
    tr = ObjectTransformer(specification=yaml.safe_load(yaml.dump(spec)), source_schemaview=SchemaView(SOURCE))
    return list(transform_spec(tr, DataLoader(data_dir, schemaview=tr.source_schemaview)))


def test_per_row_path_applies_inherited_slots(data_dir):
    """A block with no joins takes the per-row path, which gets the parent's slot derivations."""
    spec = {
        "class_derivations": {
            "Base": BASE,
            "Sample": {"is_a": "Base", "populated_from": "samples", "slot_derivations": {"sample_id": None}},
        }
    }
    assert _stream(spec, data_dir) == [{"sample_id": "S1", "tag": "from-base"}, {"sample_id": "S2", "tag": "from-base"}]


def test_join_engine_applies_inherited_slots(data_dir):
    """A block with joins takes the set-based join engine, which gets the parent's slot derivations."""
    spec = {
        "class_derivations": {
            "Base": BASE,
            "Sample": {"is_a": "Base", "populated_from": "samples", "joins": JOIN, "slot_derivations": CHILD_SLOTS},
        }
    }
    assert _stream(spec, data_dir) == [
        {"sample_id": "S1", "site": "Alpha", "tag": "from-base"},
        {"sample_id": "S2", "site": "Beta", "tag": "from-base"},
    ]


def test_joins_inherited_from_parent(data_dir):
    """A join declared on the parent applies to the child's slots."""
    spec = {
        "class_derivations": {
            "Base": {"joins": JOIN},
            "Sample": {"is_a": "Base", "populated_from": "samples", "slot_derivations": CHILD_SLOTS},
        }
    }
    assert _stream(spec, data_dir) == [{"sample_id": "S1", "site": "Alpha"}, {"sample_id": "S2", "site": "Beta"}]
