"""Tests for NMDC-style flattening patterns using linkml-map expressions.

These tests document how linkml-map can express the flattening operations
currently performed by custom Python in
``external-metadata-awareness/flatten_nmdc_collections.py``.

Each NMDC AttributeValue type has a standard flattening pattern. The flat
column naming conventions match those already used in the NMDC lakehouse
(e.g. ``depth_has_numeric_value``, ``env_broad_scale_term_id``).

Value types covered:
- QuantityValue (has_numeric_value, has_unit, has_raw_value)
- ControlledIdentifiedTermValue (term.id, term.name, has_raw_value)
- GeolocationValue (latitude, longitude, has_raw_value)
- TimestampValue (has_raw_value only)
- PersonValue (name, email, orcid)

See also:
- PR #130 (basic QuantityValue flattening)
- PR #131 (string-to-object construction, the inverse direction)
"""

import copy

from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

# ---------------------------------------------------------------------------
# Source schema: NMDC-style with nested AttributeValue types
# ---------------------------------------------------------------------------

SOURCE_SCHEMA = """\
id: https://example.org/nmdc-source
name: nmdc_source
prefixes:
  linkml: https://w3id.org/linkml/
  nmdc: https://w3id.org/nmdc/
imports:
  - linkml:types

classes:
  Biosample:
    tree_root: true
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      depth:
        range: QuantityValue
        inlined: true
      temp:
        range: QuantityValue
        inlined: true
      env_broad_scale:
        range: ControlledIdentifiedTermValue
        inlined: true
      env_local_scale:
        range: ControlledIdentifiedTermValue
        inlined: true
      env_medium:
        range: ControlledIdentifiedTermValue
        inlined: true
      lat_lon:
        range: GeolocationValue
        inlined: true
      collection_date:
        range: TimestampValue
        inlined: true
      associated_studies:
        range: string
        multivalued: true
      ecosystem:
        range: string
      ecosystem_category:
        range: string

  QuantityValue:
    attributes:
      has_raw_value:
        range: string
      has_numeric_value:
        range: float
      has_unit:
        range: string
      has_minimum_numeric_value:
        range: float
      has_maximum_numeric_value:
        range: float

  OntologyClass:
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string

  ControlledIdentifiedTermValue:
    attributes:
      has_raw_value:
        range: string
      term:
        range: OntologyClass
        inlined: true
        required: true

  GeolocationValue:
    attributes:
      has_raw_value:
        range: string
      latitude:
        range: float
        required: true
      longitude:
        range: float
        required: true

  TimestampValue:
    attributes:
      has_raw_value:
        range: string

  Study:
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      principal_investigator:
        range: PersonValue
        inlined: true
      ecosystem:
        range: string

  PersonValue:
    attributes:
      name:
        range: string
      email:
        range: string
      orcid:
        range: string
"""

# ---------------------------------------------------------------------------
# Target schema: flat lakehouse columns
# ---------------------------------------------------------------------------

TARGET_SCHEMA = """\
id: https://example.org/nmdc-flat
name: nmdc_flat
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types

classes:
  FlatBiosample:
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      # QuantityValue flattened
      depth_has_numeric_value:
        range: float
      depth_has_unit:
        range: string
      depth_has_raw_value:
        range: string
      depth_has_minimum_numeric_value:
        range: float
      depth_has_maximum_numeric_value:
        range: float
      temp_has_numeric_value:
        range: float
      temp_has_unit:
        range: string
      # ControlledIdentifiedTermValue flattened
      env_broad_scale_term_id:
        range: string
      env_broad_scale_term_name:
        range: string
      env_broad_scale_has_raw_value:
        range: string
      env_local_scale_term_id:
        range: string
      env_local_scale_term_name:
        range: string
      env_medium_term_id:
        range: string
      env_medium_term_name:
        range: string
      # GeolocationValue flattened
      lat_lon_latitude:
        range: float
      lat_lon_longitude:
        range: float
      lat_lon_has_raw_value:
        range: string
      # TimestampValue flattened
      collection_date_has_raw_value:
        range: string
      # Scalar passthrough
      ecosystem:
        range: string
      ecosystem_category:
        range: string

  FlatStudy:
    attributes:
      id:
        identifier: true
        range: string
      name:
        range: string
      pi_name:
        range: string
      pi_email:
        range: string
      pi_orcid:
        range: string
      ecosystem:
        range: string
"""

# ---------------------------------------------------------------------------
# Transformation specs
# ---------------------------------------------------------------------------

BIOSAMPLE_FLATTEN_SPEC = {
    "class_derivations": {
        "FlatBiosample": {
            "populated_from": "Biosample",
            "slot_derivations": {
                "id": {},
                "name": {},
                # QuantityValue: depth (full 5-field pattern)
                "depth_has_numeric_value": {"expr": "depth.has_numeric_value"},
                "depth_has_unit": {"expr": "depth.has_unit"},
                "depth_has_raw_value": {"expr": "depth.has_raw_value"},
                "depth_has_minimum_numeric_value": {"expr": "depth.has_minimum_numeric_value"},
                "depth_has_maximum_numeric_value": {"expr": "depth.has_maximum_numeric_value"},
                # QuantityValue: temp (partial)
                "temp_has_numeric_value": {"expr": "temp.has_numeric_value"},
                "temp_has_unit": {"expr": "temp.has_unit"},
                # ControlledIdentifiedTermValue: env triad (2-level nesting)
                "env_broad_scale_term_id": {"expr": "env_broad_scale.term.id"},
                "env_broad_scale_term_name": {"expr": "env_broad_scale.term.name"},
                "env_broad_scale_has_raw_value": {"expr": "env_broad_scale.has_raw_value"},
                "env_local_scale_term_id": {"expr": "env_local_scale.term.id"},
                "env_local_scale_term_name": {"expr": "env_local_scale.term.name"},
                "env_medium_term_id": {"expr": "env_medium.term.id"},
                "env_medium_term_name": {"expr": "env_medium.term.name"},
                # GeolocationValue: lat_lon
                "lat_lon_latitude": {"expr": "lat_lon.latitude"},
                "lat_lon_longitude": {"expr": "lat_lon.longitude"},
                "lat_lon_has_raw_value": {"expr": "lat_lon.has_raw_value"},
                # TimestampValue: collection_date
                "collection_date_has_raw_value": {"expr": "collection_date.has_raw_value"},
                # Scalar passthrough
                "ecosystem": {},
                "ecosystem_category": {},
            },
        }
    }
}

STUDY_FLATTEN_SPEC = {
    "class_derivations": {
        "FlatStudy": {
            "populated_from": "Study",
            "slot_derivations": {
                "id": {},
                "name": {},
                "pi_name": {"expr": "principal_investigator.name"},
                "pi_email": {"expr": "principal_investigator.email"},
                "pi_orcid": {"expr": "principal_investigator.orcid"},
                "ecosystem": {},
            },
        }
    }
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_transformer(spec):
    """Build an ObjectTransformer wired to the NMDC source/target schemas."""
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(copy.deepcopy(spec))
    return tr


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------

COMPLETE_BIOSAMPLE = {
    "id": "nmdc:bsm-12-abc123",
    "name": "Terrestrial soil  - Hopland",
    "depth": {
        "has_raw_value": "0.5 to 1.0 m",
        "has_numeric_value": 0.75,
        "has_unit": "m",
        "has_minimum_numeric_value": 0.5,
        "has_maximum_numeric_value": 1.0,
    },
    "temp": {
        "has_numeric_value": 18.3,
        "has_unit": "degree Celsius",
    },
    "env_broad_scale": {
        "has_raw_value": "forest biome [ENVO:01000174]",
        "term": {"id": "ENVO:01000174", "name": "forest biome"},
    },
    "env_local_scale": {
        "has_raw_value": "temperate mixed forest [ENVO:01000216]",
        "term": {"id": "ENVO:01000216", "name": "temperate mixed forest"},
    },
    "env_medium": {
        "has_raw_value": "bulk soil [ENVO:00002259]",
        "term": {"id": "ENVO:00002259", "name": "bulk soil"},
    },
    "lat_lon": {
        "has_raw_value": "38.993 -123.067",
        "latitude": 38.993,
        "longitude": -123.067,
    },
    "collection_date": {
        "has_raw_value": "2021-06-15",
    },
    "associated_studies": ["nmdc:sty-11-study01"],
    "ecosystem": "Environmental",
    "ecosystem_category": "Terrestrial",
}

SPARSE_BIOSAMPLE = {
    "id": "nmdc:bsm-12-sparse99",
    "name": "Minimal sample",
    "depth": None,
    "temp": None,
    "env_broad_scale": {
        "has_raw_value": "aquatic biome [ENVO:00002030]",
        "term": {"id": "ENVO:00002030", "name": "aquatic biome"},
    },
    "env_local_scale": None,
    "env_medium": None,
    "lat_lon": {
        "latitude": 45.0,
        "longitude": -120.0,
    },
    "collection_date": None,
    "ecosystem": None,
    "ecosystem_category": None,
}


# ===================================================================
# Biosample flattening tests
# ===================================================================


class TestBiosampleFlatten:
    """Tests for flattening Biosample to FlatBiosample."""

    def test_complete_biosample(self):
        """All fields populated: every flat column gets a value."""
        tr = _make_transformer(BIOSAMPLE_FLATTEN_SPEC)
        result = tr.map_object(COMPLETE_BIOSAMPLE, source_type="Biosample")

        # Identity
        assert result["id"] == "nmdc:bsm-12-abc123"
        assert result["name"] == "Terrestrial soil  - Hopland"

        # QuantityValue: depth (full)
        assert result["depth_has_numeric_value"] == 0.75
        assert result["depth_has_unit"] == "m"
        assert result["depth_has_raw_value"] == "0.5 to 1.0 m"
        assert result["depth_has_minimum_numeric_value"] == 0.5
        assert result["depth_has_maximum_numeric_value"] == 1.0

        # QuantityValue: temp
        assert result["temp_has_numeric_value"] == 18.3
        assert result["temp_has_unit"] == "degree Celsius"

        # ControlledIdentifiedTermValue: env triad (2-level nesting)
        assert result["env_broad_scale_term_id"] == "ENVO:01000174"
        assert result["env_broad_scale_term_name"] == "forest biome"
        assert result["env_broad_scale_has_raw_value"] == "forest biome [ENVO:01000174]"
        assert result["env_local_scale_term_id"] == "ENVO:01000216"
        assert result["env_local_scale_term_name"] == "temperate mixed forest"
        assert result["env_medium_term_id"] == "ENVO:00002259"
        assert result["env_medium_term_name"] == "bulk soil"

        # GeolocationValue
        assert result["lat_lon_latitude"] == 38.993
        assert result["lat_lon_longitude"] == -123.067
        assert result["lat_lon_has_raw_value"] == "38.993 -123.067"

        # TimestampValue
        assert result["collection_date_has_raw_value"] == "2021-06-15"

        # Scalar passthrough
        assert result["ecosystem"] == "Environmental"
        assert result["ecosystem_category"] == "Terrestrial"

    def test_sparse_biosample_null_propagation(self):
        """Null QuantityValue/ControlledTermValue propagates to None flat columns."""
        tr = _make_transformer(BIOSAMPLE_FLATTEN_SPEC)
        result = tr.map_object(SPARSE_BIOSAMPLE, source_type="Biosample")

        assert result["id"] == "nmdc:bsm-12-sparse99"

        # Null depth → all depth columns None
        assert result["depth_has_numeric_value"] is None
        assert result["depth_has_unit"] is None
        assert result["depth_has_raw_value"] is None
        assert result["depth_has_minimum_numeric_value"] is None
        assert result["depth_has_maximum_numeric_value"] is None

        # Null temp
        assert result["temp_has_numeric_value"] is None
        assert result["temp_has_unit"] is None

        # env_broad_scale populated, others null
        assert result["env_broad_scale_term_id"] == "ENVO:00002030"
        assert result["env_broad_scale_term_name"] == "aquatic biome"
        assert result["env_local_scale_term_id"] is None
        assert result["env_local_scale_term_name"] is None
        assert result["env_medium_term_id"] is None
        assert result["env_medium_term_name"] is None

        # lat_lon populated but missing has_raw_value
        assert result["lat_lon_latitude"] == 45.0
        assert result["lat_lon_longitude"] == -120.0
        assert result["lat_lon_has_raw_value"] is None

        # Null collection_date
        assert result["collection_date_has_raw_value"] is None

    def test_partial_quantity_value(self):
        """QuantityValue with some fields missing: populated fields come through."""
        tr = _make_transformer(BIOSAMPLE_FLATTEN_SPEC)
        source = {
            "id": "nmdc:bsm-12-partial",
            "name": "Partial QV",
            "depth": {"has_numeric_value": 3.0},  # no unit, no raw_value
            "temp": {"has_unit": "degree Celsius"},  # no numeric_value
            "env_broad_scale": None,
            "env_local_scale": None,
            "env_medium": None,
            "lat_lon": {"latitude": 0.0, "longitude": 0.0},
            "collection_date": None,
        }
        result = tr.map_object(source, source_type="Biosample")

        assert result["depth_has_numeric_value"] == 3.0
        assert result["depth_has_unit"] is None
        assert result["depth_has_raw_value"] is None
        assert result["temp_has_numeric_value"] is None
        assert result["temp_has_unit"] == "degree Celsius"


# ===================================================================
# Study flattening tests (PersonValue)
# ===================================================================


class TestStudyFlatten:
    """Tests for flattening Study with nested PersonValue."""

    def test_complete_study(self):
        """Study with PI: PersonValue fields are extracted."""
        tr = _make_transformer(STUDY_FLATTEN_SPEC)
        source = {
            "id": "nmdc:sty-11-study01",
            "name": "Hopland Research Station Soil Metagenome",
            "principal_investigator": {
                "name": "Elaine Faustman",
                "email": "faustman@example.org",
                "orcid": "0000-0001-2345-6789",
            },
            "ecosystem": "Environmental",
        }
        result = tr.map_object(source, source_type="Study")

        assert result["id"] == "nmdc:sty-11-study01"
        assert result["name"] == "Hopland Research Station Soil Metagenome"
        assert result["pi_name"] == "Elaine Faustman"
        assert result["pi_email"] == "faustman@example.org"
        assert result["pi_orcid"] == "0000-0001-2345-6789"
        assert result["ecosystem"] == "Environmental"

    def test_study_no_pi(self):
        """Study with no PI: PersonValue fields are None."""
        tr = _make_transformer(STUDY_FLATTEN_SPEC)
        source = {
            "id": "nmdc:sty-11-nopi",
            "name": "Study Without PI",
            "principal_investigator": None,
            "ecosystem": None,
        }
        result = tr.map_object(source, source_type="Study")

        assert result["pi_name"] is None
        assert result["pi_email"] is None
        assert result["pi_orcid"] is None

    def test_study_partial_pi(self):
        """PI with only name, no email/orcid."""
        tr = _make_transformer(STUDY_FLATTEN_SPEC)
        source = {
            "id": "nmdc:sty-11-partpi",
            "name": "Partial PI Study",
            "principal_investigator": {
                "name": "Jane Doe",
            },
        }
        result = tr.map_object(source, source_type="Study")

        assert result["pi_name"] == "Jane Doe"
        assert result["pi_email"] is None
        assert result["pi_orcid"] is None
