# [DevBounty AI]: File optimized for resolution.



```python
from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.7.0"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )




class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'linkmlmap',
     'description': 'Datamodel for LinkML schema mappings and transformations.\n'
                    '\n'
                    'A mapper generates instances of a *target* data model from\n'
                    'instances of a *source* data model. This transformation '
                    'process\n'
                    'is guided by a *TransformationSpecification*.\n'
                    '\n'
                    'The specification is independent of any one method for '
                    'transforming\n'
                    'data. It allows different approaches, including:\n'
                    '\n'
                    '- direct implementation, transforming python or json objects\n'
                    '- translation of the specification into SQL commands, to '
                    'operate on relations\n'
                    '- translation of the specification into SPARQL CONSTRUCTs, to '
                    'operate on triples\n'
                    '- translation into another specification language, such as '
                    'R2RML',
     'id': 'https://w3id.org/linkml/transformer',
     'imports': ['linkml:types'],
     'name': 'linkml-map',
     'prefixes': {'STATO': {'prefix_prefix': 'STATO',
                            'prefix_reference': 'http://purl.obolibrary.org/obo/STATO_'},
                  'dcterms': {'prefix_prefix': 'dcterms',
                              'prefix_reference': 'http://purl.org/dc/terms/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'linkmlmap': {'prefix_prefix': 'linkmlmap',
                                'prefix_reference': 'https://w3id.org/linkml/transformer/'},
                  'rdfs': {'prefix_prefix': 'rdfs',
                           'prefix_reference': 'http://www.w3.org/2000/01/rdf-schema#'},
                  'schema': {'prefix_prefix': 'schema',
                             'prefix_reference': 'http://schema.org/'},
                  'sh': {'prefix_prefix': 'sh',
                         'prefix_reference': 'http://www.w3.org/ns/shacl#'},
                  'sssom': {'prefix_prefix': 'sssom',
                            'prefix_reference': 'https://w3id.org/sssom/'}},
     'source_file': 'src/linkml_map/datamodel/transformer_model.yaml',
     'title': 'LinkML Map Data Model',
     'types': {'ClassReference': {'from_schema': 'https://w3id.org/linkml/transformer',
                                  'name': 'ClassReference',
                                  'typeof': 'string'},
               'EnumReference': {'from_schema': 'https://w3id.org/linkml/transformer',
                                 'name': 'EnumReference',
                                 'typeof': 'string'},
               'SlotReference': {'from_schema': 'https://w3id.org/linkml/transformer',
                                 'name': 'SlotReference',
                                 'typeof': 'string'}}} )

class CollectionType(str, Enum):
    SingleValued = "SingleValued"
    MultiValued = "MultiValued"
    MultiValuedList = "MultiValuedList"
    MultiValuedDict = "MultiValuedDict"


class SerializationSyntaxType(str, Enum):
    JSON = "JSON"
    YAML = "YAML"
    TURTLE = "TURTLE"


class AggregationType(str, Enum):
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    STD_DEV = "STD_DEV"
    VARIANCE = "VARIANCE"
    MEDIAN = "MEDIAN"
    MODE = "MODE"
    CUSTOM = "CUSTOM"
    SET = "SET"
    LIST = "LIST"
    ARRAY = "ARRAY"


class InvalidValueHandlingStrategy(str, Enum):
    IGNORE = "IGNORE"
    TREAT_AS_ZERO = "TREAT_AS_ZERO"
    ERROR_OUT = "ERROR_OUT"


class PivotDirectionType(str, Enum):
    ROW = "ROW"
    COLUMN = "COLUMN"