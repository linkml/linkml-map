# Auto generated from transformer_model.yaml by pythongen.py version: 0.9.0
# Generation date: 2023-03-05T13:57:57
# Schema: transformer
#
# id: https://w3id.org/linkml/transformer
# description: Datamodel for LinkML schema transformations. A transformer generates instances of a *target* data
#              model from instances of a *source* data model. This transformation process is guided by a
#              *TransformationSpecification*. The specification is independent of any one method for transforming
#              data. It allows different approaches, including: - direct implementation, transforming python or
#              json objects - translation of the specification into SQL commands, to operate on relations -
#              translation of the specification into SPARQL CONSTRUCTs, to operate on triples - translation into
#              another specification language, such as R2RML
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


class ElementDerivationName(extended_str):
    pass


class ClassDerivationName(ElementDerivationName):
    pass


class AliasedClassAlias(extended_str):
    pass


class SlotDerivationName(ElementDerivationName):
    pass


class EnumDerivationName(ElementDerivationName):
    pass


class PermissibleValueDerivationName(ElementDerivationName):
    pass


class PrefixDerivationName(ElementDerivationName):
    pass


class KeyValKey(extended_str):
    pass


class CopyDirectiveElementName(extended_str):
    pass


Any = Any

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
    slot_derivations: Optional[Union[Dict[Union[str, SlotDerivationName], Union[dict, "SlotDerivation"]], List[Union[dict, "SlotDerivation"]]]] = empty_dict()

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

        self._normalize_inlined_as_dict(slot_name="slot_derivations", slot_type=SlotDerivation, key_name="name", keyed=True)

        super().__post_init__(**kwargs)


@dataclass
class ElementDerivation(YAMLRoot):
    """
    An abstract grouping for classes that provide a specification of how to derive a target element from a source
    element.
    """
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.ElementDerivation
    class_class_curie: ClassVar[str] = "linkmltr:ElementDerivation"
    class_name: ClassVar[str] = "ElementDerivation"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.ElementDerivation

    name: Union[str, ElementDerivationName] = None
    copy_directives: Optional[Union[Dict[Union[str, CopyDirectiveElementName], Union[dict, "CopyDirective"]], List[Union[dict, "CopyDirective"]]]] = empty_dict()
    is_a: Optional[Union[str, ElementDerivationName]] = None
    mixins: Optional[Union[Dict[Union[str, ElementDerivationName], Union[dict, "ElementDerivation"]], List[Union[dict, "ElementDerivation"]]]] = empty_dict()
    value_mappings: Optional[Union[Dict[Union[str, KeyValKey], Union[dict, "KeyVal"]], List[Union[dict, "KeyVal"]]]] = empty_dict()
    expression_to_value_mappings: Optional[Union[Dict[Union[str, KeyValKey], Union[dict, "KeyVal"]], List[Union[dict, "KeyVal"]]]] = empty_dict()
    expression_to_expression_mappings: Optional[Union[Dict[Union[str, KeyValKey], Union[dict, "KeyVal"]], List[Union[dict, "KeyVal"]]]] = empty_dict()

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, ElementDerivationName):
            self.name = ElementDerivationName(self.name)

        self._normalize_inlined_as_dict(slot_name="copy_directives", slot_type=CopyDirective, key_name="element_name", keyed=True)

        if self.is_a is not None and not isinstance(self.is_a, ElementDerivationName):
            self.is_a = ElementDerivationName(self.is_a)

        self._normalize_inlined_as_dict(slot_name="mixins", slot_type=ElementDerivation, key_name="name", keyed=True)

        self._normalize_inlined_as_dict(slot_name="value_mappings", slot_type=KeyVal, key_name="key", keyed=True)

        self._normalize_inlined_as_dict(slot_name="expression_to_value_mappings", slot_type=KeyVal, key_name="key", keyed=True)

        self._normalize_inlined_as_dict(slot_name="expression_to_expression_mappings", slot_type=KeyVal, key_name="key", keyed=True)

        super().__post_init__(**kwargs)


@dataclass
class ClassDerivation(ElementDerivation):
    """
    A specification of how to derive a target class from a source class.
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
class SlotDerivation(ElementDerivation):
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
class EnumDerivation(ElementDerivation):
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
class PermissibleValueDerivation(ElementDerivation):
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
    populated_from: Optional[str] = None
    hide: Optional[Union[bool, Bool]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, PermissibleValueDerivationName):
            self.name = PermissibleValueDerivationName(self.name)

        if self.expr is not None and not isinstance(self.expr, str):
            self.expr = str(self.expr)

        if self.populated_from is not None and not isinstance(self.populated_from, str):
            self.populated_from = str(self.populated_from)

        if self.hide is not None and not isinstance(self.hide, Bool):
            self.hide = Bool(self.hide)

        super().__post_init__(**kwargs)


@dataclass
class PrefixDerivation(ElementDerivation):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.PrefixDerivation
    class_class_curie: ClassVar[str] = "linkmltr:PrefixDerivation"
    class_name: ClassVar[str] = "PrefixDerivation"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.PrefixDerivation

    name: Union[str, PrefixDerivationName] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, PrefixDerivationName):
            self.name = PrefixDerivationName(self.name)

        super().__post_init__(**kwargs)


@dataclass
class Inverse(YAMLRoot):
    """
    Used for back references
    """
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


@dataclass
class KeyVal(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.KeyVal
    class_class_curie: ClassVar[str] = "linkmltr:KeyVal"
    class_name: ClassVar[str] = "KeyVal"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.KeyVal

    key: Union[str, KeyValKey] = None
    value: Optional[Union[dict, Any]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.key):
            self.MissingRequiredField("key")
        if not isinstance(self.key, KeyValKey):
            self.key = KeyValKey(self.key)

        super().__post_init__(**kwargs)


@dataclass
class CopyDirective(YAMLRoot):
    _inherited_slots: ClassVar[List[str]] = []

    class_class_uri: ClassVar[URIRef] = LINKMLTR.CopyDirective
    class_class_curie: ClassVar[str] = "linkmltr:CopyDirective"
    class_name: ClassVar[str] = "CopyDirective"
    class_model_uri: ClassVar[URIRef] = LINKMLTR.CopyDirective

    element_name: Union[str, CopyDirectiveElementName] = None
    copy_all: Optional[Union[bool, Bool]] = None
    exclude_all: Optional[Union[bool, Bool]] = None
    exclude: Optional[Union[dict, Any]] = None
    include: Optional[Union[dict, Any]] = None
    add: Optional[Union[dict, Any]] = None

    def __post_init__(self, *_: List[str], **kwargs: Dict[str, Any]):
        if self._is_empty(self.element_name):
            self.MissingRequiredField("element_name")
        if not isinstance(self.element_name, CopyDirectiveElementName):
            self.element_name = CopyDirectiveElementName(self.element_name)

        if self.copy_all is not None and not isinstance(self.copy_all, Bool):
            self.copy_all = Bool(self.copy_all)

        if self.exclude_all is not None and not isinstance(self.exclude_all, Bool):
            self.exclude_all = Bool(self.exclude_all)

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

slots.transformationSpecification__slot_derivations = Slot(uri=LINKMLTR.slot_derivations, name="transformationSpecification__slot_derivations", curie=LINKMLTR.curie('slot_derivations'),
                   model_uri=LINKMLTR.transformationSpecification__slot_derivations, domain=None, range=Optional[Union[Dict[Union[str, SlotDerivationName], Union[dict, SlotDerivation]], List[Union[dict, SlotDerivation]]]])

slots.elementDerivation__name = Slot(uri=LINKMLTR.name, name="elementDerivation__name", curie=LINKMLTR.curie('name'),
                   model_uri=LINKMLTR.elementDerivation__name, domain=None, range=URIRef)

slots.elementDerivation__copy_directives = Slot(uri=LINKMLTR.copy_directives, name="elementDerivation__copy_directives", curie=LINKMLTR.curie('copy_directives'),
                   model_uri=LINKMLTR.elementDerivation__copy_directives, domain=None, range=Optional[Union[Dict[Union[str, CopyDirectiveElementName], Union[dict, CopyDirective]], List[Union[dict, CopyDirective]]]])

slots.elementDerivation__is_a = Slot(uri=LINKMLTR.is_a, name="elementDerivation__is_a", curie=LINKMLTR.curie('is_a'),
                   model_uri=LINKMLTR.elementDerivation__is_a, domain=None, range=Optional[Union[str, ElementDerivationName]])

slots.elementDerivation__mixins = Slot(uri=LINKMLTR.mixins, name="elementDerivation__mixins", curie=LINKMLTR.curie('mixins'),
                   model_uri=LINKMLTR.elementDerivation__mixins, domain=None, range=Optional[Union[Dict[Union[str, ElementDerivationName], Union[dict, ElementDerivation]], List[Union[dict, ElementDerivation]]]])

slots.elementDerivation__value_mappings = Slot(uri=LINKMLTR.value_mappings, name="elementDerivation__value_mappings", curie=LINKMLTR.curie('value_mappings'),
                   model_uri=LINKMLTR.elementDerivation__value_mappings, domain=None, range=Optional[Union[Dict[Union[str, KeyValKey], Union[dict, KeyVal]], List[Union[dict, KeyVal]]]])

slots.elementDerivation__expression_to_value_mappings = Slot(uri=LINKMLTR.expression_to_value_mappings, name="elementDerivation__expression_to_value_mappings", curie=LINKMLTR.curie('expression_to_value_mappings'),
                   model_uri=LINKMLTR.elementDerivation__expression_to_value_mappings, domain=None, range=Optional[Union[Dict[Union[str, KeyValKey], Union[dict, KeyVal]], List[Union[dict, KeyVal]]]])

slots.elementDerivation__expression_to_expression_mappings = Slot(uri=LINKMLTR.expression_to_expression_mappings, name="elementDerivation__expression_to_expression_mappings", curie=LINKMLTR.curie('expression_to_expression_mappings'),
                   model_uri=LINKMLTR.elementDerivation__expression_to_expression_mappings, domain=None, range=Optional[Union[Dict[Union[str, KeyValKey], Union[dict, KeyVal]], List[Union[dict, KeyVal]]]])

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

slots.permissibleValueDerivation__populated_from = Slot(uri=LINKMLTR.populated_from, name="permissibleValueDerivation__populated_from", curie=LINKMLTR.curie('populated_from'),
                   model_uri=LINKMLTR.permissibleValueDerivation__populated_from, domain=None, range=Optional[str])

slots.permissibleValueDerivation__hide = Slot(uri=LINKMLTR.hide, name="permissibleValueDerivation__hide", curie=LINKMLTR.curie('hide'),
                   model_uri=LINKMLTR.permissibleValueDerivation__hide, domain=None, range=Optional[Union[bool, Bool]])

slots.inverse__slot_name = Slot(uri=LINKMLTR.slot_name, name="inverse__slot_name", curie=LINKMLTR.curie('slot_name'),
                   model_uri=LINKMLTR.inverse__slot_name, domain=None, range=Optional[str])

slots.inverse__class_name = Slot(uri=LINKMLTR.class_name, name="inverse__class_name", curie=LINKMLTR.curie('class_name'),
                   model_uri=LINKMLTR.inverse__class_name, domain=None, range=Optional[str])

slots.keyVal__key = Slot(uri=LINKMLTR.key, name="keyVal__key", curie=LINKMLTR.curie('key'),
                   model_uri=LINKMLTR.keyVal__key, domain=None, range=URIRef)

slots.keyVal__value = Slot(uri=LINKMLTR.value, name="keyVal__value", curie=LINKMLTR.curie('value'),
                   model_uri=LINKMLTR.keyVal__value, domain=None, range=Optional[Union[dict, Any]])

slots.copyDirective__element_name = Slot(uri=LINKMLTR.element_name, name="copyDirective__element_name", curie=LINKMLTR.curie('element_name'),
                   model_uri=LINKMLTR.copyDirective__element_name, domain=None, range=URIRef)

slots.copyDirective__copy_all = Slot(uri=LINKMLTR.copy_all, name="copyDirective__copy_all", curie=LINKMLTR.curie('copy_all'),
                   model_uri=LINKMLTR.copyDirective__copy_all, domain=None, range=Optional[Union[bool, Bool]])

slots.copyDirective__exclude_all = Slot(uri=LINKMLTR.exclude_all, name="copyDirective__exclude_all", curie=LINKMLTR.curie('exclude_all'),
                   model_uri=LINKMLTR.copyDirective__exclude_all, domain=None, range=Optional[Union[bool, Bool]])

slots.copyDirective__exclude = Slot(uri=LINKMLTR.exclude, name="copyDirective__exclude", curie=LINKMLTR.curie('exclude'),
                   model_uri=LINKMLTR.copyDirective__exclude, domain=None, range=Optional[Union[dict, Any]])

slots.copyDirective__include = Slot(uri=LINKMLTR.include, name="copyDirective__include", curie=LINKMLTR.curie('include'),
                   model_uri=LINKMLTR.copyDirective__include, domain=None, range=Optional[Union[dict, Any]])

slots.copyDirective__add = Slot(uri=LINKMLTR.add, name="copyDirective__add", curie=LINKMLTR.curie('add'),
                   model_uri=LINKMLTR.copyDirective__add, domain=None, range=Optional[Union[dict, Any]])