import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, Union

from linkml_transformer.transformer.transformer import OBJECT_TYPE, Transformer

DICT_OBJ = Dict[str, Any]


logger = logging.getLogger(__name__)


@dataclass
class DuckDBTransformer(Transformer):
    """
    A Transformer that works on DuckDB data.
    """

    def transform(
        self,
        source_obj: OBJECT_TYPE,
        source_type: str = None,
        target_type: str = None,
    ) -> Union[DICT_OBJ, Any]:
        """
        Transform a source object into a target object.

        :param source_obj: source data structure
        :param source_type: source_obj instantiates this (may be class, type, or enum)
        :param target_type: target_obj instantiates this (may be class, type, or enum)
        :return: transformed data, either as type target_type or a dictionary
        """
        import duckdb

        sv = self.source_schemaview
        raise NotImplementedError("DuckDBTransformer.transform")
