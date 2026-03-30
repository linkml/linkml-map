"""Tests for merging multiple NMDC workflow activity types into a unified flat table.

Demonstrates the multiple-class_derivations-for-same-target feature (#118):
several source classes (MetagenomeSequencing, ReadQcAnalysis, MetagenomeAssembly)
are each mapped to the same ``FlatActivity`` target class, producing a single
unified stream of activity records with a ``activity_type`` discriminator column.

This is the pattern needed for the NMDC lakehouse "all activities" table,
replacing custom Python union queries across N separate MongoDB collections.

See also: PR #118 (Allow multiple class_derivations for the same target class)
"""

import copy

from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

# ---------------------------------------------------------------------------
# Source schema: multiple workflow activity classes
# ---------------------------------------------------------------------------

SOURCE_SCHEMA = """\
id: https://example.org/nmdc-activities-source
name: nmdc_activities_source
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types

classes:
  WorkflowExecution:
    abstract: true
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      was_informed_by:
        range: string
      started_at_time:
        range: string
      ended_at_time:
        range: string
      execution_resource:
        range: string
      git_url:
        range: string

  MetagenomeSequencing:
    is_a: WorkflowExecution
    attributes:
      analyte_category:
        range: string
      instrument_used:
        range: string

  ReadQcAnalysis:
    is_a: WorkflowExecution
    attributes:
      input_read_count:
        range: integer
      output_read_count:
        range: integer
      input_base_count:
        range: integer
      output_base_count:
        range: integer

  MetagenomeAssembly:
    is_a: WorkflowExecution
    attributes:
      scaffolds:
        range: integer
      scaf_bp:
        range: integer
      contigs:
        range: integer
      gap_pct:
        range: float
"""

# ---------------------------------------------------------------------------
# Target schema: unified flat activity table
# ---------------------------------------------------------------------------

TARGET_SCHEMA = """\
id: https://example.org/nmdc-activities-flat
name: nmdc_activities_flat
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types

classes:
  FlatActivity:
    attributes:
      activity_id:
        identifier: true
        range: string
      activity_type:
        range: string
      name:
        range: string
      was_informed_by:
        range: string
      started_at:
        range: string
      ended_at:
        range: string
      execution_resource:
        range: string
"""

# ---------------------------------------------------------------------------
# Transformation spec: three class_derivations for the same target
# ---------------------------------------------------------------------------

# Note: with #118, multiple class_derivations entries with the same target
# class name are stored as a list (inlined_as_list). Each derivation pulls
# from a different source class.

UNIFIED_ACTIVITY_SPEC = {
    "class_derivations": [
        {
            "name": "FlatActivity",
            "populated_from": "MetagenomeSequencing",
            "slot_derivations": {
                "activity_id": {"populated_from": "id"},
                "activity_type": {"value": "MetagenomeSequencing"},
                "name": {},
                "was_informed_by": {},
                "started_at": {"populated_from": "started_at_time"},
                "ended_at": {"populated_from": "ended_at_time"},
                "execution_resource": {},
            },
        },
        {
            "name": "FlatActivity",
            "populated_from": "ReadQcAnalysis",
            "slot_derivations": {
                "activity_id": {"populated_from": "id"},
                "activity_type": {"value": "ReadQcAnalysis"},
                "name": {},
                "was_informed_by": {},
                "started_at": {"populated_from": "started_at_time"},
                "ended_at": {"populated_from": "ended_at_time"},
                "execution_resource": {},
            },
        },
        {
            "name": "FlatActivity",
            "populated_from": "MetagenomeAssembly",
            "slot_derivations": {
                "activity_id": {"populated_from": "id"},
                "activity_type": {"value": "MetagenomeAssembly"},
                "name": {},
                "was_informed_by": {},
                "started_at": {"populated_from": "started_at_time"},
                "ended_at": {"populated_from": "ended_at_time"},
                "execution_resource": {},
            },
        },
    ]
}


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

SEQUENCING_RECORD = {
    "id": "nmdc:dgns-11-seq001",
    "name": "Sequencing of Hopland soil",
    "was_informed_by": "nmdc:omprc-11-study01",
    "started_at_time": "2021-06-15T08:00:00",
    "ended_at_time": "2021-06-15T16:00:00",
    "execution_resource": "JGI",
    "git_url": "https://github.com/example/pipeline",
    "analyte_category": "metagenome",
    "instrument_used": "Illumina NovaSeq",
}

QC_RECORD = {
    "id": "nmdc:wfrqc-11-qc001",
    "name": "Read QC for Hopland",
    "was_informed_by": "nmdc:dgns-11-seq001",
    "started_at_time": "2021-06-16T00:00:00",
    "ended_at_time": "2021-06-16T02:00:00",
    "execution_resource": "NERSC - Perlmutter",
    "git_url": "https://github.com/example/rqc",
    "input_read_count": 50000000,
    "output_read_count": 48000000,
    "input_base_count": 7500000000,
    "output_base_count": 7200000000,
}

ASSEMBLY_RECORD = {
    "id": "nmdc:wfmgas-11-asm001",
    "name": "Assembly of Hopland metagenome",
    "was_informed_by": "nmdc:wfrqc-11-qc001",
    "started_at_time": "2021-06-17T00:00:00",
    "ended_at_time": "2021-06-17T12:00:00",
    "execution_resource": "NERSC - Perlmutter",
    "git_url": "https://github.com/example/assembly",
    "scaffolds": 15000,
    "scaf_bp": 120000000,
    "contigs": 18000,
    "gap_pct": 1.5,
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_transformer(spec):
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(copy.deepcopy(spec))
    return tr


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_sequencing_to_flat_activity():
    """MetagenomeSequencing maps to FlatActivity with correct type discriminator."""
    tr = _make_transformer(UNIFIED_ACTIVITY_SPEC)
    result = tr.map_object(SEQUENCING_RECORD, source_type="MetagenomeSequencing")

    assert result["activity_id"] == "nmdc:dgns-11-seq001"
    assert result["activity_type"] == "MetagenomeSequencing"
    assert result["name"] == "Sequencing of Hopland soil"
    assert result["was_informed_by"] == "nmdc:omprc-11-study01"
    assert result["started_at"] == "2021-06-15T08:00:00"
    assert result["ended_at"] == "2021-06-15T16:00:00"
    assert result["execution_resource"] == "JGI"


def test_qc_to_flat_activity():
    """ReadQcAnalysis maps to FlatActivity; QC-specific fields are not carried."""
    tr = _make_transformer(UNIFIED_ACTIVITY_SPEC)
    result = tr.map_object(QC_RECORD, source_type="ReadQcAnalysis")

    assert result["activity_id"] == "nmdc:wfrqc-11-qc001"
    assert result["activity_type"] == "ReadQcAnalysis"
    assert result["name"] == "Read QC for Hopland"
    assert result["started_at"] == "2021-06-16T00:00:00"
    assert result["execution_resource"] == "NERSC - Perlmutter"
    # QC-specific fields are not in FlatActivity target schema
    assert "input_read_count" not in result
    assert "output_read_count" not in result


def test_assembly_to_flat_activity():
    """MetagenomeAssembly maps to FlatActivity; assembly stats not carried."""
    tr = _make_transformer(UNIFIED_ACTIVITY_SPEC)
    result = tr.map_object(ASSEMBLY_RECORD, source_type="MetagenomeAssembly")

    assert result["activity_id"] == "nmdc:wfmgas-11-asm001"
    assert result["activity_type"] == "MetagenomeAssembly"
    assert result["name"] == "Assembly of Hopland metagenome"
    assert result["was_informed_by"] == "nmdc:wfrqc-11-qc001"
    assert result["started_at"] == "2021-06-17T00:00:00"
    assert result["ended_at"] == "2021-06-17T12:00:00"
    # Assembly-specific fields are not in target
    assert "scaffolds" not in result
    assert "gap_pct" not in result


def test_all_types_produce_distinct_records():
    """Each activity type produces a distinct record with correct type tag."""
    tr = _make_transformer(UNIFIED_ACTIVITY_SPEC)

    results = [
        tr.map_object(SEQUENCING_RECORD, source_type="MetagenomeSequencing"),
        tr.map_object(QC_RECORD, source_type="ReadQcAnalysis"),
        tr.map_object(ASSEMBLY_RECORD, source_type="MetagenomeAssembly"),
    ]

    types = [r["activity_type"] for r in results]
    assert types == ["MetagenomeSequencing", "ReadQcAnalysis", "MetagenomeAssembly"]

    ids = [r["activity_id"] for r in results]
    assert len(set(ids)) == 3  # all distinct


def test_slot_rename_started_at_time():
    """started_at_time is renamed to started_at via populated_from."""
    tr = _make_transformer(UNIFIED_ACTIVITY_SPEC)
    result = tr.map_object(QC_RECORD, source_type="ReadQcAnalysis")

    assert "started_at" in result
    assert "started_at_time" not in result
    assert result["started_at"] == "2021-06-16T00:00:00"


def test_missing_optional_field():
    """Optional fields missing from source produce None in target."""
    tr = _make_transformer(UNIFIED_ACTIVITY_SPEC)
    sparse = {
        "id": "nmdc:wfrqc-11-sparse",
        "name": "Sparse QC",
        "was_informed_by": "nmdc:dgns-11-seq001",
        "started_at_time": "2021-01-01T00:00:00",
        # ended_at_time, execution_resource, git_url all missing
    }
    result = tr.map_object(sparse, source_type="ReadQcAnalysis")

    assert result["activity_id"] == "nmdc:wfrqc-11-sparse"
    assert result["activity_type"] == "ReadQcAnalysis"
    assert result["started_at"] == "2021-01-01T00:00:00"
    assert result.get("ended_at") is None
    assert result.get("execution_resource") is None
