"""Several class_derivations may share one target class (PR #118).

Each derivation pulls from a different source class and tags its output with a
discriminator, producing a single unified stream of target records. The shape is
only expressible in the *list* form of ``class_derivations`` — the mapping form
keys on the target class name, so it cannot hold the name more than once.

Generalized from the NMDC "unified activities" acceptance test contributed in
PR #145; ``test_validator`` covers that such a spec validates, but this is the
only end-to-end coverage that it transforms.
"""

import copy

import pytest
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = """\
id: https://example.org/events-source
name: events_source
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Run:
    abstract: true
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      started_at_time:
        range: string
      ended_at_time:
        range: string
  Acquisition:
    is_a: Run
    attributes:
      instrument_used:
        range: string
  QualityCheck:
    is_a: Run
    attributes:
      input_read_count:
        range: integer
  Assembly:
    is_a: Run
    attributes:
      contigs:
        range: integer
"""

TARGET_SCHEMA = """\
id: https://example.org/events-flat
name: events_flat
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  FlatEvent:
    attributes:
      event_id:
        identifier: true
        range: string
      event_type:
        range: string
      name:
        range: string
      started_at:
        range: string
      ended_at:
        range: string
"""

SOURCE_CLASSES = ["Acquisition", "QualityCheck", "Assembly"]

#: One derivation per source class, all named ``FlatEvent`` — the list form is required.
UNIFIED_SPEC = {
    "class_derivations": [
        {
            "name": "FlatEvent",
            "populated_from": source_class,
            "slot_derivations": {
                "event_id": {"populated_from": "id"},
                "event_type": {"value": source_class},
                "name": {},
                "started_at": {"populated_from": "started_at_time"},
                "ended_at": {"populated_from": "ended_at_time"},
            },
        }
        for source_class in SOURCE_CLASSES
    ]
}

#: Each record carries a field unique to its source class, to prove it isn't carried over.
RECORDS = {
    "Acquisition": {
        "id": "acq-1",
        "name": "Acquisition run",
        "started_at_time": "2021-06-15T08:00:00",
        "ended_at_time": "2021-06-15T16:00:00",
        "instrument_used": "sequencer-a",
    },
    "QualityCheck": {
        "id": "qc-1",
        "name": "Quality check",
        "started_at_time": "2021-06-16T00:00:00",
        "ended_at_time": "2021-06-16T02:00:00",
        "input_read_count": 1000,
    },
    "Assembly": {
        "id": "asm-1",
        "name": "Assembly run",
        "started_at_time": "2021-06-17T00:00:00",
        "ended_at_time": "2021-06-17T12:00:00",
        "contigs": 42,
    },
}

UNIQUE_FIELD = {"Acquisition": "instrument_used", "QualityCheck": "input_read_count", "Assembly": "contigs"}


@pytest.fixture
def transformer() -> ObjectTransformer:
    """Build a transformer over the shared source/target schemas and unified spec."""
    obj_tr = ObjectTransformer()
    obj_tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    obj_tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    obj_tr.create_transformer_specification(copy.deepcopy(UNIFIED_SPEC))
    return obj_tr


@pytest.mark.parametrize("source_class", SOURCE_CLASSES)
def test_each_source_class_maps_to_the_shared_target(transformer: ObjectTransformer, source_class: str) -> None:
    """Every derivation reaches the same target class, tagged with its own discriminator.

    :param transformer: transformer over the unified spec
    :param source_class: source class whose derivation is under test
    """
    result = transformer.map_object(RECORDS[source_class], source_type=source_class)

    assert result["event_type"] == source_class
    assert result["event_id"] == RECORDS[source_class]["id"]
    assert result["name"] == RECORDS[source_class]["name"]
    # started_at_time -> started_at: the derivations also rename slots.
    assert result["started_at"] == RECORDS[source_class]["started_at_time"]
    # Fields absent from the target schema are dropped, not carried through.
    assert UNIQUE_FIELD[source_class] not in result


def test_all_source_classes_yield_distinct_records(transformer: ObjectTransformer) -> None:
    """The derivations produce one unified stream, not overwritten single records.

    :param transformer: transformer over the unified spec
    """
    results = [transformer.map_object(RECORDS[c], source_type=c) for c in SOURCE_CLASSES]

    assert [r["event_type"] for r in results] == SOURCE_CLASSES
    assert len({r["event_id"] for r in results}) == len(SOURCE_CLASSES)


def test_missing_optional_fields_become_null(transformer: ObjectTransformer) -> None:
    """A source record missing optional slots yields nulls rather than failing.

    :param transformer: transformer over the unified spec
    """
    sparse = {"id": "qc-sparse", "name": "Sparse", "started_at_time": "2021-01-01T00:00:00"}

    result = transformer.map_object(sparse, source_type="QualityCheck")

    assert result["event_id"] == "qc-sparse"
    assert result["event_type"] == "QualityCheck"
    assert result.get("ended_at") is None
