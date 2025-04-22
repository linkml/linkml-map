"""
Tests compilation of a specification to python.
"""

import pytest
from linkml_runtime import SchemaView

from linkml_map.session import Session
from linkml_map.transformer.duckdb_transformer import DuckDBTransformer
from tests import PERSONINFO_SRC_SCHEMA, PERSONINFO_TGT_SCHEMA, PERSONINFO_TR


@pytest.fixture
def session() -> Session:
    """Instantiate a transformer session."""
    session = Session()
    session.set_source_schema(PERSONINFO_SRC_SCHEMA)
    session.set_transformer_specification(PERSONINFO_TR)
    if not session.transformer_specification:
        msg = "No specification provided."
        raise ValueError(msg)
    tr = DuckDBTransformer()
    session.set_transformer(tr)
    tr.specification = session.transformer_specification
    tr.source_schemaview = SchemaView(str(PERSONINFO_SRC_SCHEMA))
    tr.target_schemaview = SchemaView(str(PERSONINFO_TGT_SCHEMA))
    return session


def test_compile(session: Session) -> None:
    """Test compilation using the DuckDb transformer."""
    pytest.skip("TODO")
    session.transformer.map_database(":memory:")
