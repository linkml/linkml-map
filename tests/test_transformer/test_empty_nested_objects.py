"""A nested object whose slots all come out None is omitted from its parent (refs #264)."""

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
  people:
    attributes:
      pid:
        identifier: true
      code1:
      code2:
  deaths:
    attributes:
      death_pid:
        identifier: true
      code1:
      code2:
"""

TARGET = """\
id: https://example.org/t
name: t
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
      cause_of_death:
        range: CauseOfDeath
        multivalued: true
        inlined_as_list: true
      primary_cause:
        range: CauseOfDeath
        inlined: true
      arm:
        range: Arm
        inlined: true
  CauseOfDeath:
    attributes:
      cause:
      order:
        range: integer
  Arm:
    attributes:
      name:
"""


JOIN = {"deaths": {"source_key": "pid", "lookup_key": "death_pid"}}


def _cause(column: str, order: int, joins: dict | None) -> dict:
    """A CauseOfDeath whose slots are all None when *column* is empty, as in the BDC specs."""
    return {
        "CauseOfDeath": {
            **({"populated_from": "people", "joins": joins} if joins else {}),
            "slot_derivations": {
                "cause": {"expr": f'case(({{{column}}} is not None, "ICD9CM:" + str({{{column}}})))'},
                "order": {"expr": f"case(({{{column}}} is not None, {order}))"},
            },
        }
    }


def _person(joins: dict | None = None) -> dict:
    """Person slots reading code columns from the row, or from the deaths table through *joins*."""
    prefix = "deaths." if joins else ""
    return {
        "id": {"populated_from": "pid"},
        "cause_of_death": {
            "class_derivations": [_cause(f"{prefix}code1", 1, joins), _cause(f"{prefix}code2", 2, joins)]
        },
        "primary_cause": {"class_derivations": [_cause(f"{prefix}code1", 1, joins)]},
        "arm": {"class_derivations": [{"Arm": {"slot_derivations": {"name": {"value": "control"}}}}]},
    }


PER_ROW = {"Person": {"populated_from": "people", "slot_derivations": _person()}}
JOINED = {"Person": {"populated_from": "people", "slot_derivations": _person(JOIN)}}

ROWS = [
    {"pid": "P1", "code1": "410", "code2": "428"},
    {"pid": "P2", "code1": "410", "code2": None},
    {"pid": "P3", "code1": None, "code2": None},
]

ARM = {"name": "control"}
EXPECTED = [
    {
        "id": "P1",
        "cause_of_death": [{"cause": "ICD9CM:410", "order": 1}, {"cause": "ICD9CM:428", "order": 2}],
        "primary_cause": {"cause": "ICD9CM:410", "order": 1},
        "arm": ARM,
    },
    {
        "id": "P2",
        "cause_of_death": [{"cause": "ICD9CM:410", "order": 1}],
        "primary_cause": {"cause": "ICD9CM:410", "order": 1},
        "arm": ARM,
    },
    {"id": "P3", "cause_of_death": [], "primary_cause": None, "arm": ARM},
]


def _transformer(class_derivations: dict) -> ObjectTransformer:
    spec = yaml.safe_load(yaml.dump({"class_derivations": class_derivations}))
    return ObjectTransformer(
        specification=spec, source_schemaview=SchemaView(SOURCE), target_schemaview=SchemaView(TARGET)
    )


def _tsv(rows: list[dict], columns: list[str]) -> str:
    lines = ["\t".join(columns)] + ["\t".join(row[c] or "" for c in columns) for row in rows]
    return "\n".join(lines) + "\n"


def test_single_object_path():
    """map_object on one row drops the empty nested objects."""
    tr = _transformer(PER_ROW)
    assert [tr.map_object(row, source_type="people") for row in ROWS] == EXPECTED


@pytest.mark.parametrize(
    "class_derivations", [pytest.param(PER_ROW, id="per-row"), pytest.param(JOINED, id="join-engine")]
)
def test_streaming_paths(class_derivations, tmp_path):
    """Tabular streaming, with and without a joined table, drops the same empty nested objects."""
    (tmp_path / "people.tsv").write_text(_tsv(ROWS, ["pid", "code1", "code2"]))
    deaths = [{"death_pid": r["pid"], "code1": r["code1"], "code2": r["code2"]} for r in ROWS if r["code1"]]
    (tmp_path / "deaths.tsv").write_text(_tsv(deaths, ["death_pid", "code1", "code2"]))
    tr = _transformer(class_derivations)
    assert list(transform_spec(tr, DataLoader(tmp_path, schemaview=tr.source_schemaview))) == EXPECTED


MINTED_TARGET = TARGET.replace(
    "  Arm:\n",
    "  Death:\n    attributes:\n      id:\n        identifier: true\n      cause:\n  Arm:\n",
).replace("      arm:\n", "      death:\n        range: Death\n        inlined: true\n      arm:\n")


def test_minted_id_does_not_keep_an_empty_object():
    """A content-hash id is minted from the slots, so an object with no other content is still dropped."""
    death = {
        "Death": {"mint_ids": True, "slot_derivations": {"cause": {"expr": "case(({code1} is not None, {code1}))"}}}
    }
    spec = {
        "Person": {
            "populated_from": "people",
            "slot_derivations": {"id": {"populated_from": "pid"}, "death": {"class_derivations": [death]}},
        }
    }
    tr = ObjectTransformer(
        specification=yaml.safe_load(yaml.dump({"class_derivations": spec})),
        source_schemaview=SchemaView(SOURCE),
        target_schemaview=SchemaView(MINTED_TARGET),
    )
    with_cause, without = (tr.map_object(row, source_type="people") for row in (ROWS[0], ROWS[2]))
    assert with_cause["death"]["cause"] == "410"
    assert with_cause["death"]["id"]
    assert without["death"] is None
