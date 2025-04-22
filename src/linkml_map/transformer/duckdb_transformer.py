"""A Transformer that works on DuckDB data."""

import logging
from dataclasses import dataclass
from typing import Any, Optional, Union

from duckdb import DuckDBPyConnection

from linkml_map.compiler.sql_compiler import SQLCompiler
from linkml_map.transformer.transformer import OBJECT_TYPE, Transformer

DICT_OBJ = dict[str, Any]
DATABASE = Union[str, DuckDBPyConnection]


logger = logging.getLogger(__name__)


@dataclass
class DuckDBTransformer(Transformer):
    """
    A Transformer that works on DuckDB data.
    """

    def map_object(
        self,
        source_obj: OBJECT_TYPE,
        source_type: Optional[str] = None,
        target_type: Optional[str] = None,
        **kwargs: Optional[dict[str, Any]],
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
        target_database: Optional[DATABASE] = None,
        **kwargs: Optional[dict[str, Any]],
    ) -> OBJECT_TYPE:
        """
        Transform source resource.

        :param source_database:
        :param target_database:
        :param kwargs:
        :return:
        """
        import duckdb

        if target_database is None:
            target_database = source_database

        def _connect(db: DATABASE) -> DuckDBPyConnection:
            if isinstance(db, str):
                return duckdb.connect(db)
            return db

        source_connection = _connect(source_database)
        target_connection = _connect(target_database)
        sql_compiler = SQLCompiler()
        source_connection.sql(sql_compiler.create_ddl(self.source_schemaview))
        target_connection.sql(sql_compiler.create_ddl(self.target_schemaview))
        if not self.specification:
            msg = "No specification provided."
            raise ValueError(msg)
        compiled = sql_compiler.compile(self.specification)
        source_connection.execute(compiled.serialization)
