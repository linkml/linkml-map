"""Canary tests for upstream linkml/linkml-runtime bugs we work around.

Each test asserts the **correct** post-fix behavior and is marked
``xfail(strict=True)``. While the bug persists upstream, the test
xfails. When the upstream fix lands, the test starts passing and
``strict=True`` flips XPASS into a hard failure — a loud signal to
remove the local workaround.
"""

import pytest


@pytest.mark.xfail(
    strict=True,
    reason=(
        "linkml/linkml#3529: ReferenceValidator.normalize() mangles compact-key "
        "list input to inlined-dict fields as {None: ...}. When this passes, "
        "remove the PV-level branch from Transformer._pre_shape_expand_compact_keys."
    ),
)
def test_reference_validator_normalizes_compact_key_pv_list():
    """Canary: compact-key list for inlined-dict PV field normalizes correctly.

    See: https://github.com/linkml/linkml/issues/3529
    """
    from linkml_runtime.processing.referencevalidator import ReferenceValidator
    from linkml_runtime.utils.introspection import package_schemaview

    normalizer = ReferenceValidator(package_schemaview("linkml_map.datamodel.transformer_model"))
    normalizer.expand_all = True

    obj = {
        "enum_derivations": {
            "Target": {
                "populated_from": "Source",
                "permissible_value_derivations": [
                    {"red": {"sources": ["a"]}},
                ],
            },
        },
    }
    result = normalizer.normalize(obj)
    pvs = result["enum_derivations"]["Target"]["permissible_value_derivations"]

    # Expected (post-fix): compact-key name is hoisted as the dict key.
    assert None not in pvs, f"upstream still produces None-keyed entries: {pvs}"
    assert "red" in pvs, f"upstream did not hoist compact-key name: {pvs}"
