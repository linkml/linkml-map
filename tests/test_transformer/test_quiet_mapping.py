"""A correct mapping logs and warns nothing (#380)."""

import logging
import warnings

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map import ObjectTransformer

SOURCE = """\
id: https://example.org/people
name: people
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string
classes:
  Person:
    attributes:
      id:
        identifier: true
      friend:
        range: Person
      address:
        range: Address
        inlined: true
      events:
        range: Event
        multivalued: true
        inlined_as_list: true
  Address:
    attributes:
      city:
  Event:
    attributes:
      kind:
      year:
        range: integer
"""

SPEC = """\
class_derivations:
  Agent:
    populated_from: Person
    slot_derivations:
      id:
      friend:
      address:
      first_year:
        expr: |
          years = [e.year for e in src.events if e.kind == "start"]
          if years:
              target = years[0]
  Location:
    populated_from: Address
    slot_derivations:
      city:
"""

PERSON = {
    "id": "P1",
    "friend": "P2",
    "address": {"city": "Oaktown"},
    "events": [{"kind": "start", "year": 2001}, {"kind": "stop", "year": 2009}],
}


@pytest.fixture
def mapped(caplog: pytest.LogCaptureFixture) -> tuple[dict, list[str], list[str]]:
    """Map PERSON, returning the output, logged warnings and Python warnings."""
    tr = ObjectTransformer(
        specification=yaml.safe_load(SPEC), source_schemaview=SchemaView(SOURCE), unrestricted_eval=True
    )
    with caplog.at_level(logging.WARNING), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = tr.map_object(PERSON, source_type="Person")
    return out, [r.getMessage() for r in caplog.records], [str(w.message) for w in caught]


def test_mapping_values(mapped):
    """The reference stays an id, the inlined object maps through its derivation, and the statements run."""
    out, _, _ = mapped
    assert out == {"id": "P1", "friend": "P2", "address": {"city": "Oaktown"}, "first_year": 2001}


def test_mapping_logs_nothing(mapped):
    """No 'Unexpected' for the reference, no 'Unknown target range' for the class-ranged slot."""
    _, logged, _ = mapped
    assert logged == []


def test_statement_expression_skips_restricted_evaluator(mapped):
    """A statement block goes straight to the unrestricted evaluator, so simpleeval never warns about it."""
    _, _, python_warnings = mapped
    assert python_warnings == []
