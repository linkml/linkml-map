# Auto generated from transformer_model.yaml by pythongen.py version: 0.9.0
# Generation date: 2022-07-07T23:08:06
# Schema: transformer
#
# id: https://w3id.org/linkml/transformer
# description: Datamodel for LinkML schema transformations
# license: https://creativecommons.org/publicdomain/zero/1.0/

import dataclasses
import sys
import re
from jsonasobj2 import JsonObj, as_dict
from typing import Optional, List, Union, Dict, ClassVar, Any
from dataclasses import dataclass
from linkml_runtime.linkml_model.meta import EnumDefinition, PermissibleValue, PvFormulaOptions

from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.metamodelcore import empty_list, empty_dict, bnode
from linkml_runtime.utils.yamlutils import YAMLRoot, extended_str, extended_float, extended_int
from linkml_runtime.utils.dataclass_extensions_376 import dataclasses_init_fn_with_kwargs
from linkml_runtime.utils.formatutils import camelcase, underscore, sfx
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from rdflib import Namespace, URIRef
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.linkml_model.types import Boolean, String
from linkml_runtime.utils.metamodelcore import Bool

metamodel_version = "1.7.0"
version = None

# Overwrite dataclasses _init_fn to add **kwargs in __init__
dataclasses._init_fn = dataclasses_init_fn_with_kwargs

# Namespaces
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
TR = CurieNamespace('tr', 'https://w3id.org/linkml/transformer/')
DEFAULT_ = TR


# Types

# Class references
class ClassDerivationName(extended_str):
    pass


class AliasedClassAlias(extended_str):
    pass


class SlotDerivationName(extended_str):
    pass


@dataclass
class TransformationSpecification(YAMLRoot):
    """
    A collection of mappings between source and target classes
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TR.TransformationSpecification
    class_class_curie: ClassVar[str] = "tr:TransformationSpecification"
    class_name: ClassVar[str] = "TransformationSpecification"
    class_model_uri: ClassVar[URIRef] = TR.TransformationSpecification

    id: Optional[str] = None
    title: Optional[str] = None
    prefixes: Optional[str] = None
    source_schema: Optional[str] = None
    target_schema: Optional[str] = None
    class_derivations: Optional[Union[Dict[Union[str, ClassDerivationName], Union[dict, "ClassDerivation"]], List[Union[dict, "ClassDerivation"]]]] = empty_dict()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self.id is not None and not isinstance(self.id, str):
            self.id = str(self.id)

        if self.title is not None and not isinstance(self.title, str):
            self.title = str(self.title)

        if self.prefixes is not None and not isinstance(self.prefixes, str):
            self.prefixes = str(self.prefixes)

        if self.source_schema is not None and not isinstance(self.source_schema, str):
            self.source_schema = str(self.source_schema)

        if self.target_schema is not None and not isinstance(self.target_schema, str):
            self.target_schema = str(self.target_schema)

        self._normalize_inlined_as_dict(slot_name="class_derivations", slot_type=ClassDerivation, key_name="name", keyed=True)

        super().__post_init__(**kwargs)


@dataclass
class ClassDerivation(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TR.ClassDerivation
    class_class_curie: ClassVar[str] = "tr:ClassDerivation"
    class_name: ClassVar[str] = "ClassDerivation"
    class_model_uri: ClassVar[URIRef] = TR.ClassDerivation

    name: Union[str, ClassDerivationName] = None
    populated_from: Optional[str] = None
    joins: Optional[Union[Dict[Union[str, AliasedClassAlias], Union[dict, "AliasedClass"]], List[Union[dict, "AliasedClass"]]]] = empty_dict()
    slot_derivations: Optional[Union[Dict[Union[str, SlotDerivationName], Union[dict, "SlotDerivation"]], List[Union[dict, "SlotDerivation"]]]] = empty_dict()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, ClassDerivationName):
            self.name = ClassDerivationName(self.name)

        if self.populated_from is not None and not isinstance(self.populated_from, str):
            self.populated_from = str(self.populated_from)

        self._normalize_inlined_as_dict(slot_name="joins", slot_type=AliasedClass, key_name="alias", keyed=True)

        self._normalize_inlined_as_dict(slot_name="slot_derivations", slot_type=SlotDerivation, key_name="name", keyed=True)

        super().__post_init__(**kwargs)


@dataclass
class AliasedClass(YAMLRoot):
    """
    alias-class key value pairs for classes
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TR.AliasedClass
    class_class_curie: ClassVar[str] = "tr:AliasedClass"
    class_name: ClassVar[str] = "AliasedClass"
    class_model_uri: ClassVar[URIRef] = TR.AliasedClass

    alias: Union[str, AliasedClassAlias] = None
    class_named: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.alias):
            self.MissingRequiredField("alias")
        if not isinstance(self.alias, AliasedClassAlias):
            self.alias = AliasedClassAlias(self.alias)

        if self.class_named is not None and not isinstance(self.class_named, str):
            self.class_named = str(self.class_named)

        super().__post_init__(**kwargs)


@dataclass
class SlotDerivation(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TR.SlotDerivation
    class_class_curie: ClassVar[str] = "tr:SlotDerivation"
    class_name: ClassVar[str] = "SlotDerivation"
    class_model_uri: ClassVar[URIRef] = TR.SlotDerivation

    name: Union[str, SlotDerivationName] = None
    populated_from: Optional[str] = None
    expr: Optional[str] = None
    inverse_of: Optional[Union[dict, "Inverse"]] = None
    hide: Optional[Union[bool, Bool]] = None
    type_designator: Optional[Union[bool, Bool]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, SlotDerivationName):
            self.name = SlotDerivationName(self.name)

        if self.populated_from is not None and not isinstance(self.populated_from, str):
            self.populated_from = str(self.populated_from)

        if self.expr is not None and not isinstance(self.expr, str):
            self.expr = str(self.expr)

        if self.inverse_of is not None and not isinstance(self.inverse_of, Inverse):
            self.inverse_of = Inverse(**as_dict(self.inverse_of))

        if self.hide is not None and not isinstance(self.hide, Bool):
            self.hide = Bool(self.hide)

        if self.type_designator is not None and not isinstance(self.type_designator, Bool):
            self.type_designator = Bool(self.type_designator)

        super().__post_init__(**kwargs)


@dataclass
class Inverse(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = TR.Inverse
    class_class_curie: ClassVar[str] = "tr:Inverse"
    class_name: ClassVar[str] = "Inverse"
    class_model_uri: ClassVar[URIRef] = TR.Inverse

    slot_name: Optional[str] = None
    class_name: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self.slot_name is not None and not isinstance(self.slot_name, str):
            self.slot_name = str(self.slot_name)

        if self.class_name is not None and not isinstance(self.class_name, str):
            self.class_name = str(self.class_name)

        super().__post_init__(**kwargs)


# Enumerations


# Slots
class slots:
    pass

slots.transformationSpecification__id = Slot(uri=TR.id, name="transformationSpecification__id", curie=TR.curie('id'),
                   model_uri=TR.transformationSpecification__id, domain=None, range=Optional[str])

slots.transformationSpecification__title = Slot(uri=TR.title, name="transformationSpecification__title", curie=TR.curie('title'),
                   model_uri=TR.transformationSpecification__title, domain=None, range=Optional[str])

slots.transformationSpecification__prefixes = Slot(uri=TR.prefixes, name="transformationSpecification__prefixes", curie=TR.curie('prefixes'),
                   model_uri=TR.transformationSpecification__prefixes, domain=None, range=Optional[str])

slots.transformationSpecification__source_schema = Slot(uri=TR.source_schema, name="transformationSpecification__source_schema", curie=TR.curie('source_schema'),
                   model_uri=TR.transformationSpecification__source_schema, domain=None, range=Optional[str])

slots.transformationSpecification__target_schema = Slot(uri=TR.target_schema, name="transformationSpecification__target_schema", curie=TR.curie('target_schema'),
                   model_uri=TR.transformationSpecification__target_schema, domain=None, range=Optional[str])

slots.transformationSpecification__class_derivations = Slot(uri=TR.class_derivations, name="transformationSpecification__class_derivations", curie=TR.curie('class_derivations'),
                   model_uri=TR.transformationSpecification__class_derivations, domain=None, range=Optional[Union[Dict[Union[str, ClassDerivationName], Union[dict, ClassDerivation]], List[Union[dict, ClassDerivation]]]])

slots.classDerivation__name = Slot(uri=TR.name, name="classDerivation__name", curie=TR.curie('name'),
                   model_uri=TR.classDerivation__name, domain=None, range=URIRef)

slots.classDerivation__populated_from = Slot(uri=TR.populated_from, name="classDerivation__populated_from", curie=TR.curie('populated_from'),
                   model_uri=TR.classDerivation__populated_from, domain=None, range=Optional[str])

slots.classDerivation__joins = Slot(uri=TR.joins, name="classDerivation__joins", curie=TR.curie('joins'),
                   model_uri=TR.classDerivation__joins, domain=None, range=Optional[Union[Dict[Union[str, AliasedClassAlias], Union[dict, AliasedClass]], List[Union[dict, AliasedClass]]]])

slots.classDerivation__slot_derivations = Slot(uri=TR.slot_derivations, name="classDerivation__slot_derivations", curie=TR.curie('slot_derivations'),
                   model_uri=TR.classDerivation__slot_derivations, domain=None, range=Optional[Union[Dict[Union[str, SlotDerivationName], Union[dict, SlotDerivation]], List[Union[dict, SlotDerivation]]]])

slots.aliasedClass__alias = Slot(uri=TR.alias, name="aliasedClass__alias", curie=TR.curie('alias'),
                   model_uri=TR.aliasedClass__alias, domain=None, range=URIRef)

slots.aliasedClass__class_named = Slot(uri=TR.class_named, name="aliasedClass__class_named", curie=TR.curie('class_named'),
                   model_uri=TR.aliasedClass__class_named, domain=None, range=Optional[str])

slots.slotDerivation__name = Slot(uri=TR.name, name="slotDerivation__name", curie=TR.curie('name'),
                   model_uri=TR.slotDerivation__name, domain=None, range=URIRef)

slots.slotDerivation__populated_from = Slot(uri=TR.populated_from, name="slotDerivation__populated_from", curie=TR.curie('populated_from'),
                   model_uri=TR.slotDerivation__populated_from, domain=None, range=Optional[str])

slots.slotDerivation__expr = Slot(uri=TR.expr, name="slotDerivation__expr", curie=TR.curie('expr'),
                   model_uri=TR.slotDerivation__expr, domain=None, range=Optional[str])

slots.slotDerivation__inverse_of = Slot(uri=TR.inverse_of, name="slotDerivation__inverse_of", curie=TR.curie('inverse_of'),
                   model_uri=TR.slotDerivation__inverse_of, domain=None, range=Optional[Union[dict, Inverse]])

slots.slotDerivation__hide = Slot(uri=TR.hide, name="slotDerivation__hide", curie=TR.curie('hide'),
                   model_uri=TR.slotDerivation__hide, domain=None, range=Optional[Union[bool, Bool]])

slots.slotDerivation__type_designator = Slot(uri=TR.type_designator, name="slotDerivation__type_designator", curie=TR.curie('type_designator'),
                   model_uri=TR.slotDerivation__type_designator, domain=None, range=Optional[Union[bool, Bool]])

slots.inverse__slot_name = Slot(uri=TR.slot_name, name="inverse__slot_name", curie=TR.curie('slot_name'),
                   model_uri=TR.inverse__slot_name, domain=None, range=Optional[str])

slots.inverse__class_name = Slot(uri=TR.class_name, name="inverse__class_name", curie=TR.curie('class_name'),
                   model_uri=TR.inverse__class_name, domain=None, range=Optional[str])