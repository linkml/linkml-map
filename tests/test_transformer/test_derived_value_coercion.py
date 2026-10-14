"""``expr:`` and ``value:`` results are coerced to the target slot like ``populated_from`` (#364).

Cardinality and datatype follow the target slot, not how the value was derived.
"""

import textwrap
from decimal import Decimal

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map.transformer.object_transformer import ObjectTransformer

SOURCE_SCHEMA = textwrap.dedent("""\
    id: https://example.org/derived-source
    name: derived_source
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: derived_source
    default_range: string
    imports: [linkml:types]
    classes:
      Row:
        attributes:
          tag: {}
          amount: {}
""")

TARGET_SCHEMA = textwrap.dedent("""\
    id: https://example.org/derived-target
    name: derived_target
    prefixes: {linkml: 'https://w3id.org/linkml/'}
    default_prefix: derived_target
    default_range: string
    imports: [linkml:types]
    classes:
      Out:
        attributes:
          tags_pf: {multivalued: true}
          tags_expr: {multivalued: true}
          tags_value: {multivalued: true}
          amt_pf: {range: decimal}
          amt_expr: {range: decimal}
          amt_value: {range: decimal}
          count_value: {range: integer}
          label_expr: {}
          amt_text: {range: decimal}
""")

SPEC = textwrap.dedent("""\
    id: derived-value-coercion
    class_derivations:
      Out:
        populated_from: Row
        slot_derivations:
          tags_pf: {populated_from: tag}
          tags_expr: {expr: "{tag}"}
          tags_value: {value: a}
          amt_pf: {populated_from: amount}
          amt_expr: {expr: "{amount}"}
          amt_value: {value: "5.0"}
          count_value: {value: 7}
          label_expr: {expr: "1 + 1"}
          amt_text: {expr: "{amount}", range: string}
""")

ROW = {"tag": "y", "amount": "5.0"}


def _map(*, with_target: bool = True) -> dict:
    tr = ObjectTransformer()
    tr.source_schemaview = SchemaView(SOURCE_SCHEMA)
    if with_target:
        tr.target_schemaview = SchemaView(TARGET_SCHEMA)
    tr.create_transformer_specification(yaml.safe_load(SPEC))
    return tr.map_object(ROW, "Row")


@pytest.mark.parametrize("slot", ["tags_pf", "tags_expr"])
def test_scalar_into_multivalued_becomes_a_list(slot: str) -> None:
    """A scalar headed for a multivalued slot is wrapped, however it was derived."""
    assert _map()[slot] == ["y"]


def test_constant_into_multivalued_becomes_a_list() -> None:
    assert _map()["tags_value"] == ["a"]


@pytest.mark.parametrize("slot", ["amt_pf", "amt_expr", "amt_value"])
def test_decimal_target_gets_a_decimal(slot: str) -> None:
    assert _map()[slot] == Decimal("5.0")


def test_constant_takes_the_target_type() -> None:
    """A ``value:`` constant isn't forced to a string; the target slot types it."""
    assert _map()["count_value"] == 7


def test_expr_result_into_string_slot_is_stringified() -> None:
    assert _map()["label_expr"] == "2"


def test_spec_range_overrides_target_schema() -> None:
    assert _map()["amt_text"] == "5.0"


def test_no_target_schema_leaves_derived_values_alone() -> None:
    """Without a target schema, only spec ranges coerce."""
    out = _map(with_target=False)
    assert out["tags_expr"] == "y"
    assert out["count_value"] == 7
    assert out["label_expr"] == 2
    assert out["amt_text"] == "5.0"
