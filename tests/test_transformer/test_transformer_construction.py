"""Transformers take a specification and schemas in the constructor, as paths or loaded objects."""

import pytest
import yaml
from linkml_runtime import SchemaView

from linkml_map import ObjectTransformer, load_specification
from linkml_map.transformer.duckdb_transformer import DuckDBTransformer
from linkml_map.transformer.transformer import Transformer
from tests import PERSONINFO_DATA, PERSONINFO_SRC_SCHEMA, PERSONINFO_TGT_SCHEMA, PERSONINFO_TR


def _mapped_person(tr: ObjectTransformer) -> dict:
    return tr.map_object(yaml.safe_load(PERSONINFO_DATA.read_text()), source_type="Person")


@pytest.fixture(scope="module")
def expected_person() -> dict:
    """The mapped person from a transformer set up field by field. Personinfo's expressions need unrestricted eval."""
    tr = ObjectTransformer(unrestricted_eval=True)
    tr.source_schemaview = SchemaView(str(PERSONINFO_SRC_SCHEMA))
    tr.load_transformer_specification(PERSONINFO_TR)
    return _mapped_person(tr)


@pytest.mark.parametrize(
    ("spec", "schema"),
    [
        (str(PERSONINFO_TR), str(PERSONINFO_SRC_SCHEMA)),
        (PERSONINFO_TR, PERSONINFO_SRC_SCHEMA),
        (lambda: yaml.safe_load(PERSONINFO_TR.read_text()), lambda: SchemaView(str(PERSONINFO_SRC_SCHEMA))),
        (lambda: load_specification(PERSONINFO_TR), lambda: SchemaView(str(PERSONINFO_SRC_SCHEMA))),
    ],
    ids=["str", "path", "dict-schemaview", "spec-schemaview"],
)
def test_constructor_input_forms_map_alike(spec, schema, expected_person):
    """Every input form maps a person the same as a transformer set up field by field."""
    tr = ObjectTransformer(
        specification=spec() if callable(spec) else spec,
        source_schemaview=schema() if callable(schema) else schema,
        unrestricted_eval=True,
    )
    assert _mapped_person(tr) == expected_person


@pytest.mark.parametrize("transformer_class", [ObjectTransformer, DuckDBTransformer])
def test_constructor_loads_paths(transformer_class: type[Transformer]):
    """Both transformers load the specification and both schemas from paths."""
    tr = transformer_class(
        specification=PERSONINFO_TR,
        source_schemaview=PERSONINFO_SRC_SCHEMA,
        target_schemaview=str(PERSONINFO_TGT_SCHEMA),
    )
    assert tr.specification == load_specification(PERSONINFO_TR)
    assert tr.source_schemaview.schema.name == SchemaView(str(PERSONINFO_SRC_SCHEMA)).schema.name
    assert tr.target_schemaview.schema.name == SchemaView(str(PERSONINFO_TGT_SCHEMA)).schema.name


def test_constructor_keeps_spec_messages():
    """A dict given to the constructor keeps its load-time scan messages, as the load methods do."""
    slot_derivations = {"id": {"derived_from": "id"}}
    spec = {"class_derivations": {"Agent": {"populated_from": "Person", "slot_derivations": slot_derivations}}}
    with pytest.warns(DeprecationWarning, match="derived_from"):
        tr = ObjectTransformer(specification=spec)
    assert [m.category for m in tr.spec_messages] == ["deprecated"]
