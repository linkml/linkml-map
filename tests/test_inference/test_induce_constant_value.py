"""Constant ``value:`` slot derivations in ``induce_missing_values``.

A constant has no source slot, so inference must not synthesize an identity
``populated_from`` for it — otherwise the derived spec fails semantic validation
with a spurious "not found on source class" error (#338).
"""

import textwrap

import yaml
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.validator import validate_spec_semantics

SOURCE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/constant-source
    name: constant_source
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: constant_source
    default_range: string
    imports: [linkml:types]
    classes:
      Row:
        attributes:
          person_id: {identifier: true}
          note: {}
""")

SPEC = textwrap.dedent("""\
    id: constant-value
    class_derivations:
      Out:
        populated_from: Row
        slot_derivations:
          person_id:
            populated_from: person_id
          note:
            populated_from: note
          tag:
            value: 7
""")


def _transformer() -> ObjectTransformer:
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    tr.create_transformer_specification(yaml.safe_load(SPEC))
    return tr


def test_constant_value_gets_no_populated_from():
    """The derived spec leaves a constant's ``populated_from`` unset."""
    out = next(cd for cd in _transformer().derived_specification.class_derivations if cd.name == "Out")
    assert out.slot_derivations["tag"].populated_from is None
    assert out.slot_derivations["note"].populated_from == "note"


def test_constant_value_derived_spec_validates_clean():
    """Validating the derived spec, as map-data does, reports no errors for a constant."""
    tr = _transformer()
    messages = validate_spec_semantics(
        tr.derived_specification.model_dump(exclude_none=True),
        source_schemaview=tr.source_schemaview,
    )
    assert [m for m in messages if m.severity == "error"] == []


def test_constant_value_still_emitted():
    """The constant still lands in the output."""
    tr = _transformer()
    assert tr.map_object({"person_id": "p1", "note": "hi"}, "Row") == {"person_id": "p1", "note": "hi", "tag": 7}
