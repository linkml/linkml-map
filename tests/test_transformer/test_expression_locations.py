"""Tests for expression-location enumeration + the model-driven completeness guard.

The guard is the important one: it introspects the transformer model and fails if
a new expression-bearing field is added without being registered, so the join
normalizer can't silently miss a cross-table reference hiding in a new field.
"""

from __future__ import annotations

from pathlib import Path

from linkml_runtime import SchemaView

import linkml_map
from linkml_map.datamodel.transformer_model import (
    EnumDerivation,
    KeyVal,
    PermissibleValueDerivation,
    SlotDerivation,
)
from linkml_map.utils.expression_locations import (
    MAPPING_EXPR_FIELDS,
    SELF_EXPR_FIELDS,
    iter_expressions,
)

MODEL_PATH = Path(linkml_map.__file__).parent / "datamodel" / "transformer_model.yaml"


# --- iter_expressions: pulls exprs from every field shape ---


def test_self_expr_on_slot():
    assert list(iter_expressions(SlotDerivation(name="x", expr="{A.col}"))) == ["{A.col}"]


def test_self_expr_on_enum_and_pv():
    assert list(iter_expressions(EnumDerivation(name="e", expr="{B.col}"))) == ["{B.col}"]
    assert list(iter_expressions(PermissibleValueDerivation(name="pv", expr="{C.col}"))) == ["{C.col}"]


def test_expression_mappings_values_are_exprs():
    sd = SlotDerivation(name="x", expression_mappings={"k": KeyVal(key="k", value="{A.col}")})
    assert list(iter_expressions(sd)) == ["{A.col}"]


def test_expression_to_value_mappings_keys_are_exprs():
    sd = SlotDerivation(
        name="x",
        expression_to_value_mappings={"{A.col} == 1": KeyVal(key="{A.col} == 1", value="literal")},
    )
    assert list(iter_expressions(sd)) == ["{A.col} == 1"]


def test_expression_to_expression_mappings_both_sides():
    sd = SlotDerivation(
        name="x",
        expression_to_expression_mappings={"{A.k}": KeyVal(key="{A.k}", value="{B.v}")},
    )
    assert set(iter_expressions(sd)) == {"{A.k}", "{B.v}"}


def test_value_mappings_are_not_expressions():
    """Literal value_mappings must not be treated as expressions."""
    sd = SlotDerivation(name="x", value_mappings={"F": KeyVal(key="F", value="Female")})
    assert list(iter_expressions(sd)) == []


def test_all_fields_combined():
    sd = SlotDerivation(
        name="x",
        expr="{A.a}",
        expression_mappings={"k": KeyVal(key="k", value="{B.b}")},
    )
    assert set(iter_expressions(sd)) == {"{A.a}", "{B.b}"}


def test_empty_derivation_yields_nothing():
    assert list(iter_expressions(SlotDerivation(name="x"))) == []


# --- completeness guard: model introspection ---


def test_every_model_expression_field_is_registered():
    """Fail if the model has an expression-bearing field not registered in expression_locations.

    Candidate detection uses the model's own conventions: a ``string`` slot whose
    description names the "expression language" is a self-expr field; a ``KeyVal``
    slot whose name starts with ``expression`` is an expression mapping. Adding a
    new such field to transformer_model.yaml will fail this test until it's
    registered (and handled by the normalizer).
    """
    sv = SchemaView(str(MODEL_PATH))
    self_fields: set[str] = set()
    mapping_fields: set[str] = set()
    for cls in sv.all_classes():
        for slot in sv.class_induced_slots(cls):
            desc = slot.description or ""
            if slot.range == "string" and "expression language" in desc:
                self_fields.add(slot.name)
            if slot.range == "KeyVal" and slot.name.startswith("expression"):
                mapping_fields.add(slot.name)

    unregistered_self = self_fields - set(SELF_EXPR_FIELDS)
    assert not unregistered_self, f"unregistered self-expr fields: {sorted(unregistered_self)}"

    assert mapping_fields == set(MAPPING_EXPR_FIELDS), (
        f"expression mapping fields in model {sorted(mapping_fields)} != registered {sorted(MAPPING_EXPR_FIELDS)}"
    )
