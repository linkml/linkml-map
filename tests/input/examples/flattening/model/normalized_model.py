# Auto generated from mapping_norm.yaml by pythongen.py version: 0.9.0
# Generation date: 2022-10-11T21:55:30
# Schema: mappings_norm
#
# id: https://w3id.org/linkml/examples/mappings-norm
# description: Normalized Mappings
# license: https://creativecommons.org/publicdomain/zero/1.0/

import dataclasses
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Union

from jsonasobj2 import as_dict
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.dataclass_extensions_376 import (
    dataclasses_init_fn_with_kwargs,
)
from linkml_runtime.utils.metamodelcore import empty_dict, empty_list
from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.yamlutils import YAMLRoot, extended_str
from rdflib import URIRef

metamodel_version = "1.7.0"
version = None

# Overwrite dataclasses _init_fn to add **kwargs in __init__
dataclasses._init_fn = dataclasses_init_fn_with_kwargs

# Namespaces
LINKML = CurieNamespace("linkml", "https://w3id.org/linkml/")
MAPPINGS = CurieNamespace("mappings", "https://w3id.org/linkml/examples/mappings-norm/")
RDF = CurieNamespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = CurieNamespace("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
SCHEMA = CurieNamespace("schema", "http://example.org/UNKNOWN/schema/")
SKOS = CurieNamespace("skos", "http://example.org/UNKNOWN/skos/")
XSD = CurieNamespace("xsd", "http://www.w3.org/2001/XMLSchema#")
DEFAULT_ = MAPPINGS


# Types


# Class references
class EntityId(extended_str):
    pass


@dataclass
class MappingSet(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = MAPPINGS.MappingSet
    class_class_curie: ClassVar[str] = "mappings:MappingSet"
    class_name: ClassVar[str] = "MappingSet"
    class_model_uri: ClassVar[URIRef] = MAPPINGS.MappingSet

    mappings: Optional[Union[Union[dict, "Mapping"], List[Union[dict, "Mapping"]]]] = empty_list()
    entities: Optional[
        Union[
            Dict[Union[str, EntityId], Union[dict, "Entity"]],
            List[Union[dict, "Entity"]],
        ]
    ] = empty_dict()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if not isinstance(self.mappings, list):
            self.mappings = [self.mappings] if self.mappings is not None else []
        self.mappings = [
            v if isinstance(v, Mapping) else Mapping(**as_dict(v)) for v in self.mappings
        ]

        self._normalize_inlined_as_dict(
            slot_name="entities", slot_type=Entity, key_name="id", keyed=True
        )

        super().__post_init__(**kwargs)


@dataclass
class Mapping(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = MAPPINGS.Mapping
    class_class_curie: ClassVar[str] = "mappings:Mapping"
    class_name: ClassVar[str] = "Mapping"
    class_model_uri: ClassVar[URIRef] = MAPPINGS.Mapping

    subject: Optional[Union[str, EntityId]] = None
    object: Optional[Union[str, EntityId]] = None
    predicate: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self.subject is not None and not isinstance(self.subject, EntityId):
            self.subject = EntityId(self.subject)

        if self.object is not None and not isinstance(self.object, EntityId):
            self.object = EntityId(self.object)

        if self.predicate is not None and not isinstance(self.predicate, str):
            self.predicate = str(self.predicate)

        super().__post_init__(**kwargs)


@dataclass
class Entity(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = MAPPINGS.Entity
    class_class_curie: ClassVar[str] = "mappings:Entity"
    class_name: ClassVar[str] = "Entity"
    class_model_uri: ClassVar[URIRef] = MAPPINGS.Entity

    id: Union[str, EntityId] = None
    name: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, EntityId):
            self.id = EntityId(self.id)

        if self.name is not None and not isinstance(self.name, str):
            self.name = str(self.name)

        super().__post_init__(**kwargs)


# Enumerations


# Slots
class slots:
    pass


slots.id = Slot(
    uri=SCHEMA.identifier,
    name="id",
    curie=SCHEMA.curie("identifier"),
    model_uri=MAPPINGS.id,
    domain=None,
    range=URIRef,
)

slots.name = Slot(
    uri=RDFS.label,
    name="name",
    curie=RDFS.curie("label"),
    model_uri=MAPPINGS.name,
    domain=None,
    range=Optional[str],
)

slots.predicate = Slot(
    uri=MAPPINGS.predicate,
    name="predicate",
    curie=MAPPINGS.curie("predicate"),
    model_uri=MAPPINGS.predicate,
    domain=None,
    range=Optional[str],
)

slots.subject = Slot(
    uri=MAPPINGS.subject,
    name="subject",
    curie=MAPPINGS.curie("subject"),
    model_uri=MAPPINGS.subject,
    domain=None,
    range=Optional[Union[str, EntityId]],
)

slots.object = Slot(
    uri=MAPPINGS.object,
    name="object",
    curie=MAPPINGS.curie("object"),
    model_uri=MAPPINGS.object,
    domain=None,
    range=Optional[Union[str, EntityId]],
)

slots.mappingSet__mappings = Slot(
    uri=MAPPINGS.mappings,
    name="mappingSet__mappings",
    curie=MAPPINGS.curie("mappings"),
    model_uri=MAPPINGS.mappingSet__mappings,
    domain=None,
    range=Optional[Union[Union[dict, Mapping], List[Union[dict, Mapping]]]],
)

slots.mappingSet__entities = Slot(
    uri=MAPPINGS.entities,
    name="mappingSet__entities",
    curie=MAPPINGS.curie("entities"),
    model_uri=MAPPINGS.mappingSet__entities,
    domain=None,
    range=Optional[
        Union[Dict[Union[str, EntityId], Union[dict, Entity]], List[Union[dict, Entity]]]
    ],
)
