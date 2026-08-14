"""A Transformer that works on DuckDB data."""

import logging
from dataclasses import dataclass
from typing import Any

from duckdb import DuckDBPyConnection

from linkml_map.compiler.sql_compiler import SQLCompiler
from linkml_map.transformer.transformer import OBJECT_TYPE, Transformer

DICT_OBJ = dict[str, Any]
DATABASE = str | DuckDBPyConnection


logger = logging.getLogger(__name__)


@dataclass
class DuckDBTransformer(Transformer):
    """
    A Transformer that works on DuckDB data.
    """

    def map_object(
        self,
        source_obj: OBJECT_TYPE,
        source_type: str | None = None,
        target_type: str | None = None,
        **kwargs: Any,
    ) -> OBJECT_TYPE:
        """
        Transform a source object into a target object.

        :param source_obj: source data structure
        :param source_type: source_obj instantiates this (may be class, type, or enum)
        :param target_type: target_obj instantiates this (may be class, type, or enum)
        :return: transformed data, either as type target_type or a dictionary
        """
        msg = "DuckDBTransformer.transform"
        raise NotImplementedError(msg)

    def map_database(
        self,
        source_database: DATABASE,
        target_database: DATABASE | None = None,
        **kwargs: Any,
    ) -> DuckDBPyConnection:
        """
        Transform source resource.

        :param source_database: Database holding the source tables, as a path or an open
            connection.  Target tables are created alongside them and populated in place.
        :param target_database: Must be unset or equal to *source_database*.
        :param kwargs:
        :return: The connection the target tables were written to.
        :raises NotImplementedError: If a target database distinct from the source is given.
        """
        import duckdb

        def _connect(db: DATABASE) -> DuckDBPyConnection:
            if isinstance(db, str):
                return duckdb.connect(db)
            return db

        if target_database is not None and target_database != source_database:
            # The compiled INSERTs name source tables unqualified, so they only resolve on a
            # connection that holds both source and target.  Spanning two databases needs an
            # ATTACH and qualified names; until that exists, say so rather than silently
            # leaving the target empty.
            msg = (
                "map_database cannot yet write to a database separate from the source. "
                "Omit target_database to transform in place."
            )
            raise NotImplementedError(msg)

        # One connection, not two: connecting twice to the same path (and especially to
        # ':memory:') yields two independent databases, so the target would never see the rows.
        connection = _connect(source_database)
        sql_compiler = SQLCompiler(
            source_schemaview=self.source_schemaview,
            target_schemaview=self.target_schemaview,
        )
        connection.sql(sql_compiler.create_ddl(self.source_schemaview))
        connection.sql(sql_compiler.create_ddl(self.target_schemaview))
        if not self.specification:
            msg = "No specification provided."
            raise ValueError(msg)
        compiled = sql_compiler.compile(self.specification)
        connection.execute(compiled.serialization)
        return connection
