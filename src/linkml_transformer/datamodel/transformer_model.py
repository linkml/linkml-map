# Auto generated from transformer_model.yaml by pythongen.py version: 0.9.0
# Generation date: 2022-10-11T21:43:16
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
LINKMLTR = CurieNamespace('linkmltr', 'https://w3id.org/linkml/transformer/')
DEFAULT_ = LINKMLTR


# Types

# Class references
class TransformationSpecificationId(extended_str):
    pass


class ClassDerivationName(extended_str):
    pass


class AliasedClassAlias(extended_str):
    pass


class SlotDerivationName(extended_str):
    pass


class EnumDerivationName(extended_str):
    pass


class PermissibleValueDerivationName(extended_str):
    pass


@dataclass
class TransformationSpecification(YAMLRoot):
    """
    A collection of mappings between source and target classes
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.TransformationSpecification
    class_class_curie: ClassVar[str] = "linkmltr:TransformationSpecification"
    class_name: ClassVar[str] = "TransformationSpecification"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.TransformationSpecification

    id: Union[str, TransformationSpecificationId] = None
    title: Optional[str] = None
    prefixes: Optional[str] = None
    source_schema: Optional[str] = None
    target_schema: Optional[str] = None
    class_derivations: Optional[Union[Dict[Union[str, ClassDerivationName], Union[dict, "ClassDerivation"]], List[Union[dict, "ClassDerivation"]]]] = empty_dict()
    enum_derivations: Optional[Union[Dict[Union[str, EnumDerivationName], Union[dict, "EnumDerivation"]], List[Union[dict, "EnumDerivation"]]]] = empty_dict()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, TransformationSpecificationId):
            self.id = TransformationSpecificationId(self.id)

        if self.title is not None and not isinstance(self.title, str):
            self.title = str(self.title)

        if self.prefixes is not None and not isinstance(self.prefixes, str):
            self.prefixes = str(self.prefixes)

        if self.source_schema is not None and not isinstance(self.source_schema, str):
            self.source_schema = str(self.source_schema)

        if self.target_schema is not None and not isinstance(self.target_schema, str):
            self.target_schema = str(self.target_schema)

        self._normalize_inlined_as_dict(slot_name="class_derivations", slot_type=ClassDerivation, key_name="name", keyed=True)

        self._normalize_inlined_as_dict(slot_name="enum_derivations", slot_type=EnumDerivation, key_name="name", keyed=True)

        super().__post_init__(**kwargs)


@dataclass
class ClassDerivation(YAMLRoot):
    """
    A specification of how to derive a target class from a source class
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.ClassDerivation
    class_class_curie: ClassVar[str] = "linkmltr:ClassDerivation"
    class_name: ClassVar[str] = "ClassDerivation"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.ClassDerivation

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

    class_class_uri: ClassVar[URIRef] = LINKMLTR.AliasedClass
    class_class_curie: ClassVar[str] = "linkmltr:AliasedClass"
    class_name: ClassVar[str] = "AliasedClass"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.AliasedClass

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
    """
    A specification of how to derive the value of a target slot from a source slot
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.SlotDerivation
    class_class_curie: ClassVar[str] = "linkmltr:SlotDerivation"
    class_name: ClassVar[str] = "SlotDerivation"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.SlotDerivation

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
class EnumDerivation(YAMLRoot):
    """
    A specification of how to derive the value of a target enum from a source enum
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.EnumDerivation
    class_class_curie: ClassVar[str] = "linkmltr:EnumDerivation"
    class_name: ClassVar[str] = "EnumDerivation"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.EnumDerivation

    name: Union[str, EnumDerivationName] = None
    populated_from: Optional[str] = None
    expr: Optional[str] = None
    hide: Optional[Union[bool, Bool]] = None
    permissible_value_derivations: Optional[Union[Dict[Union[str, PermissibleValueDerivationName], Union[dict, "PermissibleValueDerivation"]], List[Union[dict, "PermissibleValueDerivation"]]]] = empty_dict()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, EnumDerivationName):
            self.name = EnumDerivationName(self.name)

        if self.populated_from is not None and not isinstance(self.populated_from, str):
            self.populated_from = str(self.populated_from)

        if self.expr is not None and not isinstance(self.expr, str):
            self.expr = str(self.expr)

        if self.hide is not None and not isinstance(self.hide, Bool):
            self.hide = Bool(self.hide)

        self._normalize_inlined_as_dict(slot_name="permissible_value_derivations", slot_type=PermissibleValueDerivation, key_name="name", keyed=True)

        super().__post_init__(**kwargs)


@dataclass
class PermissibleValueDerivation(YAMLRoot):
    """
    A specification of how to derive the value of a PV from a source enum
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.PermissibleValueDerivation
    class_class_curie: ClassVar[str] = "linkmltr:PermissibleValueDerivation"
    class_name: ClassVar[str] = "PermissibleValueDerivation"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.PermissibleValueDerivation

    name: Union[str, PermissibleValueDerivationName] = None
    expr: Optional[str] = None
    hide: Optional[Union[bool, Bool]] = None
    populated_from: Optional[str] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, PermissibleValueDerivationName):
            self.name = PermissibleValueDerivationName(self.name)

        if self.expr is not None and not isinstance(self.expr, str):
            self.expr = str(self.expr)

        if self.hide is not None and not isinstance(self.hide, Bool):
            self.hide = Bool(self.hide)

        if self.populated_from is not None and not isinstance(self.populated_from, str):
            self.populated_from = str(self.populated_from)

        super().__post_init__(**kwargs)


@dataclass
class Inverse(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.Inverse
    class_class_curie: ClassVar[str] = "linkmltr:Inverse"
    class_name: ClassVar[str] = "Inverse"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.Inverse

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

slots.transformationSpecification__id = Slot(uri=LINKMLTR.id, name="transformationSpecification__id", curie=LINKMLTR.curie('id'),
                   model_uri=LINKMLTR.transformationSpecification__id, domain=None, range=URIRef)

slots.transformationSpecification__title = Slot(uri=LINKMLTR.title, name="transformationSpecification__title", curie=LINKMLTR.curie('title'),
                   model_uri=LINKMLTR.transformationSpecification__title, domain=None, range=Optional[str])

slots.transformationSpecification__prefixes = Slot(uri=LINKMLTR.prefixes, name="transformationSpecification__prefixes", curie=LINKMLTR.curie('prefixes'),
                   model_uri=LINKMLTR.transformationSpecification__prefixes, domain=None, range=Optional[str])

slots.transformationSpecification__source_schema = Slot(uri=LINKMLTR.source_schema, name="transformationSpecification__source_schema", curie=LINKMLTR.curie('source_schema'),
                   model_uri=LINKMLTR.transformationSpecification__source_schema, domain=None, range=Optional[str])

slots.transformationSpecification__target_schema = Slot(uri=LINKMLTR.target_schema, name="transformationSpecification__target_schema", curie=LINKMLTR.curie('target_schema'),
                   model_uri=LINKMLTR.transformationSpecification__target_schema, domain=None, range=Optional[str])

slots.transformationSpecification__class_derivations = Slot(uri=LINKMLTR.class_derivations, name="transformationSpecification__class_derivations", curie=LINKMLTR.curie('class_derivations'),
                   model_uri=LINKMLTR.transformationSpecification__class_derivations, domain=None, range=Optional[Union[Dict[Union[str, ClassDerivationName], Union[dict, ClassDerivation]], List[Union[dict, ClassDerivation]]]])

slots.transformationSpecification__enum_derivations = Slot(uri=LINKMLTR.enum_derivations, name="transformationSpecification__enum_derivations", curie=LINKMLTR.curie('enum_derivations'),
                   model_uri=LINKMLTR.transformationSpecification__enum_derivations, domain=None, range=Optional[Union[Dict[Union[str, EnumDerivationName], Union[dict, EnumDerivation]], List[Union[dict, EnumDerivation]]]])

slots.classDerivation__name = Slot(uri=LINKMLTR.name, name="classDerivation__name", curie=LINKMLTR.curie('name'),
                   model_uri=LINKMLTR.classDerivation__name, domain=None, range=URIRef)

slots.classDerivation__populated_from = Slot(uri=LINKMLTR.populated_from, name="classDerivation__populated_from", curie=LINKMLTR.curie('populated_from'),
                   model_uri=LINKMLTR.classDerivation__populated_from, domain=None, range=Optional[str])

slots.classDerivation__joins = Slot(uri=LINKMLTR.joins, name="classDerivation__joins", curie=LINKMLTR.curie('joins'),
                   model_uri=LINKMLTR.classDerivation__joins, domain=None, range=Optional[Union[Dict[Union[str, AliasedClassAlias], Union[dict, AliasedClass]], List[Union[dict, AliasedClass]]]])

slots.classDerivation__slot_derivations = Slot(uri=LINKMLTR.slot_derivations, name="classDerivation__slot_derivations", curie=LINKMLTR.curie('slot_derivations'),
                   model_uri=LINKMLTR.classDerivation__slot_derivations, domain=None, range=Optional[Union[Dict[Union[str, SlotDerivationName], Union[dict, SlotDerivation]], List[Union[dict, SlotDerivation]]]])

slots.aliasedClass__alias = Slot(uri=LINKMLTR.alias, name="aliasedClass__alias", curie=LINKMLTR.curie('alias'),
                   model_uri=LINKMLTR.aliasedClass__alias, domain=None, range=URIRef)

slots.aliasedClass__class_named = Slot(uri=LINKMLTR.class_named, name="aliasedClass__class_named", curie=LINKMLTR.curie('class_named'),
                   model_uri=LINKMLTR.aliasedClass__class_named, domain=None, range=Optional[str])

slots.slotDerivation__name = Slot(uri=LINKMLTR.name, name="slotDerivation__name", curie=LINKMLTR.curie('name'),
                   model_uri=LINKMLTR.slotDerivation__name, domain=None, range=URIRef)

slots.slotDerivation__populated_from = Slot(uri=LINKMLTR.populated_from, name="slotDerivation__populated_from", curie=LINKMLTR.curie('populated_from'),
                   model_uri=LINKMLTR.slotDerivation__populated_from, domain=None, range=Optional[str])

slots.slotDerivation__expr = Slot(uri=LINKMLTR.expr, name="slotDerivation__expr", curie=LINKMLTR.curie('expr'),
                   model_uri=LINKMLTR.slotDerivation__expr, domain=None, range=Optional[str])

slots.slotDerivation__inverse_of = Slot(uri=LINKMLTR.inverse_of, name="slotDerivation__inverse_of", curie=LINKMLTR.curie('inverse_of'),
                   model_uri=LINKMLTR.slotDerivation__inverse_of, domain=None, range=Optional[Union[dict, Inverse]])

slots.slotDerivation__hide = Slot(uri=LINKMLTR.hide, name="slotDerivation__hide", curie=LINKMLTR.curie('hide'),
                   model_uri=LINKMLTR.slotDerivation__hide, domain=None, range=Optional[Union[bool, Bool]])

slots.slotDerivation__type_designator = Slot(uri=LINKMLTR.type_designator, name="slotDerivation__type_designator", curie=LINKMLTR.curie('type_designator'),
                   model_uri=LINKMLTR.slotDerivation__type_designator, domain=None, range=Optional[Union[bool, Bool]])

slots.enumDerivation__name = Slot(uri=LINKMLTR.name, name="enumDerivation__name", curie=LINKMLTR.curie('name'),
                   model_uri=LINKMLTR.enumDerivation__name, domain=None, range=URIRef)

slots.enumDerivation__populated_from = Slot(uri=LINKMLTR.populated_from, name="enumDerivation__populated_from", curie=LINKMLTR.curie('populated_from'),
                   model_uri=LINKMLTR.enumDerivation__populated_from, domain=None, range=Optional[str])

slots.enumDerivation__expr = Slot(uri=LINKMLTR.expr, name="enumDerivation__expr", curie=LINKMLTR.curie('expr'),
                   model_uri=LINKMLTR.enumDerivation__expr, domain=None, range=Optional[str])

slots.enumDerivation__hide = Slot(uri=LINKMLTR.hide, name="enumDerivation__hide", curie=LINKMLTR.curie('hide'),
                   model_uri=LINKMLTR.enumDerivation__hide, domain=None, range=Optional[Union[bool, Bool]])

slots.enumDerivation__permissible_value_derivations = Slot(uri=LINKMLTR.permissible_value_derivations, name="enumDerivation__permissible_value_derivations", curie=LINKMLTR.curie('permissible_value_derivations'),
                   model_uri=LINKMLTR.enumDerivation__permissible_value_derivations, domain=None, range=Optional[Union[Dict[Union[str, PermissibleValueDerivationName], Union[dict, PermissibleValueDerivation]], List[Union[dict, PermissibleValueDerivation]]]])

slots.permissibleValueDerivation__name = Slot(uri=LINKMLTR.name, name="permissibleValueDerivation__name", curie=LINKMLTR.curie('name'),
                   model_uri=LINKMLTR.permissibleValueDerivation__name, domain=None, range=URIRef)

slots.permissibleValueDerivation__expr = Slot(uri=LINKMLTR.expr, name="permissibleValueDerivation__expr", curie=LINKMLTR.curie('expr'),
                   model_uri=LINKMLTR.permissibleValueDerivation__expr, domain=None, range=Optional[str])

slots.permissibleValueDerivation__hide = Slot(uri=LINKMLTR.hide, name="permissibleValueDerivation__hide", curie=LINKMLTR.curie('hide'),
                   model_uri=LINKMLTR.permissibleValueDerivation__hide, domain=None, range=Optional[Union[bool, Bool]])

slots.permissibleValueDerivation__populated_from = Slot(uri=LINKMLTR.populated_from, name="permissibleValueDerivation__populated_from", curie=LINKMLTR.curie('populated_from'),
                   model_uri=LINKMLTR.permissibleValueDerivation__populated_from, domain=None, range=Optional[str])

slots.inverse__slot_name = Slot(uri=LINKMLTR.slot_name, name="inverse__slot_name", curie=LINKMLTR.curie('slot_name'),
                   model_uri=LINKMLTR.inverse__slot_name, domain=None, range=Optional[str])

slots.inverse__class_name = Slot(uri=LINKMLTR.class_name, name="inverse__class_name", curie=LINKMLTR.curie('class_name'),
                   model_uri=LINKMLTR.inverse__class_name, domain=None, range=Optional[str])