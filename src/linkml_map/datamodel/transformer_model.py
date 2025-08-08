from __future__ import annotations

import re
import sys
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Dict, List, Literal, Optional, Union

from pydantic.version import VERSION as PYDANTIC_VERSION

if int(PYDANTIC_VERSION[0]) >= 2:
    from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator
else:
    from pydantic import BaseModel, Field, validator

metamodel_version = "None"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )
    pass


class LinkMLMeta(RootModel):
    root: Dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key: str):
        return getattr(self.root, key)

    def __getitem__(self, key: str):
        return self.root[key]

    def __setitem__(self, key: str, value):
        self.root[key] = value


linkml_meta = LinkMLMeta(
    {
        "default_prefix": "https://w3id.org/linkml/transformer/",
        "description": "Datamodel for LinkML schema mappings and transformations.\n"
        "\n"
        "A mapper generates instances of a *target* data model from\n"
        "instances of a *source* data model. This transformation "
        "process\n"
        "is guided by a *TransformationSpecification*.\n"
        "\n"
        "The specification is independent of any one method for "
        "transforming\n"
        "data. It allows different approaches, including:\n"
        "\n"
        "- direct implementation, transforming python or json objects\n"
        "- translation of the specification into SQL commands, to "
        "operate on relations\n"
        "- translation of the specification into SPARQL CONSTRUCTs, to "
        "operate on triples\n"
        "- translation into another specification language, such as "
        "R2RML",
        "id": "https://w3id.org/linkml/transformer",
        "name": "linkml-map",
    }
)


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
    MELT = "MELT"
    UNMELT = "UNMELT"


class SpecificationComponent(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"abstract": True, "from_schema": "https://w3id.org/linkml/transformer"}
    )

    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )


class TransformationSpecification(SpecificationComponent):
    """
    A collection of mappings between source and target classes
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer", "tree_root": True}
    )

    id: Optional[str] = Field(
        None,
        description="""Unique identifier for this transformation specification""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "id",
                "domain_of": ["TransformationSpecification"],
                "slot_uri": "schema:identifier",
            }
        },
    )
    title: Optional[str] = Field(
        None,
        description="""human readable title for this transformation specification""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "title",
                "domain_of": ["TransformationSpecification"],
                "slot_uri": "dcterms:title",
            }
        },
    )
    prefixes: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""maps prefixes to URL expansions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "prefixes",
                "domain_of": ["TransformationSpecification"],
                "slot_uri": "sh:declare",
            }
        },
    )
    source_schema: Optional[str] = Field(
        None,
        description="""name of the schema that describes the source (input) objects""",
        json_schema_extra={
            "linkml_meta": {"alias": "source_schema", "domain_of": ["TransformationSpecification"]}
        },
    )
    target_schema: Optional[str] = Field(
        None,
        description="""name of the schema that describes the target (output) objects""",
        json_schema_extra={
            "linkml_meta": {"alias": "target_schema", "domain_of": ["TransformationSpecification"]}
        },
    )
    class_derivations: Optional[Dict[str, ClassDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of classes in the target schema from classes in the source schema.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "class_derivations",
                "domain_of": ["TransformationSpecification"],
            }
        },
    )
    enum_derivations: Optional[Dict[str, EnumDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of enums in the target schema""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "enum_derivations",
                "domain_of": ["TransformationSpecification"],
            }
        },
    )
    slot_derivations: Optional[Dict[str, SlotDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of top level slots in the target schema""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "slot_derivations",
                "domain_of": ["TransformationSpecification", "ClassDerivation"],
            }
        },
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(default_factory=dict)
    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )


class ElementDerivation(SpecificationComponent):
    """
    An abstract grouping for classes that provide a specification of how to  derive a target element from a source element.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"abstract": True, "from_schema": "https://w3id.org/linkml/transformer"}
    )

    name: str = Field(
        ...,
        description="""Name of the element in the target schema""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "name",
                "domain_of": [
                    "ElementDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(
        default_factory=dict,
        json_schema_extra={
            "linkml_meta": {"alias": "copy_directives", "domain_of": ["ElementDerivation"]}
        },
    )
    overrides: Optional[Any] = Field(
        None,
        description="""overrides source schema slots""",
        json_schema_extra={
            "linkml_meta": {"alias": "overrides", "domain_of": ["ElementDerivation"]}
        },
    )
    is_a: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "is_a",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:is_a",
            }
        },
    )
    mixins: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "mixins",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:mixins",
            }
        },
    )
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
        json_schema_extra={
            "linkml_meta": {"alias": "value_mappings", "domain_of": ["ElementDerivation"]}
        },
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_value_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_expression_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    mirror_source: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "mirror_source", "domain_of": ["ElementDerivation"]}
        },
    )
    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )


class ClassDerivation(ElementDerivation):
    """
    A specification of how to derive a target class from a source class.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    populated_from: Optional[str] = Field(
        None,
        description="""Name of the class in the source schema""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "populated_from",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    sources: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "sources",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    joins: Optional[Dict[str, AliasedClass]] = Field(
        default_factory=dict,
        description="""Additional classes to be joined to derive instances of the target class""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "joins",
                "comments": ["not yet implemented"],
                "domain_of": ["ClassDerivation"],
            }
        },
    )
    slot_derivations: Optional[Dict[str, SlotDerivation]] = Field(
        default_factory=dict,
        json_schema_extra={
            "linkml_meta": {
                "alias": "slot_derivations",
                "domain_of": ["TransformationSpecification", "ClassDerivation"],
            }
        },
    )
    target_definition: Optional[Any] = Field(
        None,
        description="""LinkML class definition object for this slot.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "target_definition",
                "comments": ["currently defined as Any to avoid coupling with metamodel"],
                "domain_of": ["ClassDerivation", "SlotDerivation"],
            }
        },
    )
    name: str = Field(
        ...,
        description="""Name of the element in the target schema""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "name",
                "domain_of": [
                    "ElementDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(
        default_factory=dict,
        json_schema_extra={
            "linkml_meta": {"alias": "copy_directives", "domain_of": ["ElementDerivation"]}
        },
    )
    overrides: Optional[Any] = Field(
        None,
        description="""overrides source schema slots""",
        json_schema_extra={
            "linkml_meta": {"alias": "overrides", "domain_of": ["ElementDerivation"]}
        },
    )
    is_a: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "is_a",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:is_a",
            }
        },
    )
    mixins: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "mixins",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:mixins",
            }
        },
    )
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
        json_schema_extra={
            "linkml_meta": {"alias": "value_mappings", "domain_of": ["ElementDerivation"]}
        },
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_value_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_expression_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    mirror_source: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "mirror_source", "domain_of": ["ElementDerivation"]}
        },
    )
    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )

class ObjectDerivation(BaseModel):
    class_derivations: Dict[str, ClassDerivation]

class AliasedClass(ConfiguredBaseModel):
    """
    alias-class key value pairs for classes
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    alias: str = Field(
        ...,
        description="""name of the class to be aliased""",
        json_schema_extra={"linkml_meta": {"alias": "alias", "domain_of": ["AliasedClass"]}},
    )
    class_named: Optional[str] = Field(
        None,
        description="""local alias for the class""",
        json_schema_extra={"linkml_meta": {"alias": "class_named", "domain_of": ["AliasedClass"]}},
    )


class SlotDerivation(ElementDerivation):
    """
    A specification of how to derive the value of a target slot from a source slot
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    name: str = Field(
        ...,
        description="""Target slot name""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "name",
                "domain_of": [
                    "ElementDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    populated_from: Optional[str] = Field(
        None,
        description="""Source slot name""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "populated_from",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    sources: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "sources",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    object_derivations: Optional[List[ObjectDerivation]] = None
    derived_from: Optional[List[str]] = Field(
        default_factory=list,
        description="""Source slots that are used to derive this slot. This can be computed from the expr, if the expr is declarative.""",
        json_schema_extra={
            "linkml_meta": {"alias": "derived_from", "domain_of": ["SlotDerivation"]}
        },
    )
    expr: Optional[str] = Field(
        None,
        description="""An expression to be evaluated on the source object to derive the target slot. Should be specified using the LinkML expression language.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expr",
                "domain_of": ["SlotDerivation", "EnumDerivation", "PermissibleValueDerivation"],
            }
        },
    )
    value: Optional[Any] = Field(
        None,
        description="""A constant value to assign to this slot, overriding all other derivations""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "value",
                "domain_of": ["SlotDerivation"]
            }
        },
    )
    range: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "range",
                "domain_of": ["SlotDerivation"],
                "slot_uri": "linkml:range",
            }
        },
    )
    unit_conversion: Optional[UnitConversionConfiguration] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "unit_conversion", "domain_of": ["SlotDerivation"]}
        },
    )
    inverse_of: Optional[Inverse] = Field(
        None,
        description="""Used to specify a class-slot tuple that is the inverse of the derived/target slot. This is used primarily for mapping to relational databases or formalisms that do not allow multiple values. The class representing the repeated element has a foreign key slot inserted in that 'back references' the original multivalued slot.""",
        json_schema_extra={"linkml_meta": {"alias": "inverse_of", "domain_of": ["SlotDerivation"]}},
    )
    hide: Optional[bool] = Field(
        None,
        description="""True if this is suppressed""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "hide",
                "domain_of": ["SlotDerivation", "EnumDerivation", "PermissibleValueDerivation"],
            }
        },
    )
    type_designator: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "type_designator", "domain_of": ["SlotDerivation"]}
        },
    )
    target_definition: Optional[Any] = Field(
        None,
        description="""LinkML definition object for this slot.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "target_definition",
                "comments": ["currently defined as Any to avoid coupling with metamodel"],
                "domain_of": ["ClassDerivation", "SlotDerivation"],
            }
        },
    )
    cast_collection_as: Optional[CollectionType] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "cast_collection_as", "domain_of": ["SlotDerivation"]}
        },
    )
    dictionary_key: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "dictionary_key", "domain_of": ["SlotDerivation"]}
        },
    )
    stringification: Optional[StringificationConfiguration] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "stringification", "domain_of": ["SlotDerivation"]}
        },
    )
    aggregation_operation: Optional[AggregationOperation] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "aggregation_operation", "domain_of": ["SlotDerivation"]}
        },
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(
        default_factory=dict,
        json_schema_extra={
            "linkml_meta": {"alias": "copy_directives", "domain_of": ["ElementDerivation"]}
        },
    )
    overrides: Optional[Any] = Field(
        None,
        description="""overrides source schema slots""",
        json_schema_extra={
            "linkml_meta": {"alias": "overrides", "domain_of": ["ElementDerivation"]}
        },
    )
    is_a: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "is_a",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:is_a",
            }
        },
    )
    mixins: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "mixins",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:mixins",
            }
        },
    )
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
        json_schema_extra={
            "linkml_meta": {"alias": "value_mappings", "domain_of": ["ElementDerivation"]}
        },
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_value_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_expression_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    mirror_source: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "mirror_source", "domain_of": ["ElementDerivation"]}
        },
    )
    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )


class EnumDerivation(ElementDerivation):
    """
    A specification of how to derive the value of a target enum from a source enum
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    name: str = Field(
        ...,
        description="""Target enum name""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "name",
                "domain_of": [
                    "ElementDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    populated_from: Optional[str] = Field(
        None,
        description="""Source enum name""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "populated_from",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    sources: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "sources",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    expr: Optional[str] = Field(
        None,
        description="""An expression to be evaluated on the source object to derive the target slot. Should be specified using the LinkML expression language.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expr",
                "domain_of": ["SlotDerivation", "EnumDerivation", "PermissibleValueDerivation"],
            }
        },
    )
    hide: Optional[bool] = Field(
        None,
        description="""True if this is suppressed""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "hide",
                "domain_of": ["SlotDerivation", "EnumDerivation", "PermissibleValueDerivation"],
            }
        },
    )
    permissible_value_derivations: Optional[Dict[str, PermissibleValueDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of PVs in the target schema""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "permissible_value_derivations",
                "domain_of": ["EnumDerivation"],
            }
        },
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(
        default_factory=dict,
        json_schema_extra={
            "linkml_meta": {"alias": "copy_directives", "domain_of": ["ElementDerivation"]}
        },
    )
    overrides: Optional[Any] = Field(
        None,
        description="""overrides source schema slots""",
        json_schema_extra={
            "linkml_meta": {"alias": "overrides", "domain_of": ["ElementDerivation"]}
        },
    )
    is_a: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "is_a",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:is_a",
            }
        },
    )
    mixins: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "mixins",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:mixins",
            }
        },
    )
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
        json_schema_extra={
            "linkml_meta": {"alias": "value_mappings", "domain_of": ["ElementDerivation"]}
        },
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_value_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_expression_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    mirror_source: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "mirror_source", "domain_of": ["ElementDerivation"]}
        },
    )
    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )


class PermissibleValueDerivation(ElementDerivation):
    """
    A specification of how to derive the value of a PV from a source enum
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://w3id.org/linkml/transformer",
            "todos": [
                "this is currently under-specified. We will need boolean "
                "combinators to express if-then-else"
            ],
        }
    )

    name: str = Field(
        ...,
        description="""Target permissible value text""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "name",
                "domain_of": [
                    "ElementDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    expr: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "expr",
                "domain_of": ["SlotDerivation", "EnumDerivation", "PermissibleValueDerivation"],
            }
        },
    )
    populated_from: Optional[str] = Field(
        None,
        description="""Source permissible value""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "populated_from",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    sources: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "sources",
                "domain_of": [
                    "ClassDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    hide: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "hide",
                "domain_of": ["SlotDerivation", "EnumDerivation", "PermissibleValueDerivation"],
            }
        },
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(
        default_factory=dict,
        json_schema_extra={
            "linkml_meta": {"alias": "copy_directives", "domain_of": ["ElementDerivation"]}
        },
    )
    overrides: Optional[Any] = Field(
        None,
        description="""overrides source schema slots""",
        json_schema_extra={
            "linkml_meta": {"alias": "overrides", "domain_of": ["ElementDerivation"]}
        },
    )
    is_a: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "is_a",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:is_a",
            }
        },
    )
    mixins: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "mixins",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:mixins",
            }
        },
    )
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
        json_schema_extra={
            "linkml_meta": {"alias": "value_mappings", "domain_of": ["ElementDerivation"]}
        },
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_value_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_expression_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    mirror_source: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "mirror_source", "domain_of": ["ElementDerivation"]}
        },
    )
    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )


class PrefixDerivation(ElementDerivation):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    name: str = Field(
        ...,
        description="""Name of the element in the target schema""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "name",
                "domain_of": [
                    "ElementDerivation",
                    "SlotDerivation",
                    "EnumDerivation",
                    "PermissibleValueDerivation",
                ],
            }
        },
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(
        default_factory=dict,
        json_schema_extra={
            "linkml_meta": {"alias": "copy_directives", "domain_of": ["ElementDerivation"]}
        },
    )
    overrides: Optional[Any] = Field(
        None,
        description="""overrides source schema slots""",
        json_schema_extra={
            "linkml_meta": {"alias": "overrides", "domain_of": ["ElementDerivation"]}
        },
    )
    is_a: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "is_a",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:is_a",
            }
        },
    )
    mixins: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {
                "alias": "mixins",
                "domain_of": ["ElementDerivation"],
                "slot_uri": "linkml:mixins",
            }
        },
    )
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
        json_schema_extra={
            "linkml_meta": {"alias": "value_mappings", "domain_of": ["ElementDerivation"]}
        },
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_value_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "expression_to_expression_mappings",
                "domain_of": ["ElementDerivation"],
            }
        },
    )
    mirror_source: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "mirror_source", "domain_of": ["ElementDerivation"]}
        },
    )
    description: Optional[str] = Field(
        None,
        description="""description of the specification component""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "description",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "dcterms:description",
            }
        },
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
        json_schema_extra={
            "linkml_meta": {"alias": "implements", "domain_of": ["SpecificationComponent"]}
        },
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "comments",
                "domain_of": ["SpecificationComponent"],
                "slot_uri": "rdfs:comment",
            }
        },
    )


class UnitConversionConfiguration(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    target_unit: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "target_unit", "domain_of": ["UnitConversionConfiguration"]}
        },
    )
    target_unit_scheme: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "target_unit_scheme",
                "domain_of": ["UnitConversionConfiguration"],
                "examples": [{"value": "ucum"}],
            }
        },
    )
    source_unit: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "source_unit", "domain_of": ["UnitConversionConfiguration"]}
        },
    )
    source_unit_scheme: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "source_unit_scheme",
                "domain_of": ["UnitConversionConfiguration"],
                "examples": [{"value": "ucum"}],
            }
        },
    )
    source_unit_slot: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "source_unit_slot",
                "domain_of": ["UnitConversionConfiguration"],
            }
        },
    )
    source_magnitude_slot: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "source_magnitude_slot",
                "domain_of": ["UnitConversionConfiguration"],
            }
        },
    )
    target_unit_slot: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "target_unit_slot",
                "domain_of": ["UnitConversionConfiguration"],
            }
        },
    )
    target_magnitude_slot: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "target_magnitude_slot",
                "domain_of": ["UnitConversionConfiguration"],
            }
        },
    )


class StringificationConfiguration(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    delimiter: Optional[str] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "delimiter",
                "domain_of": ["StringificationConfiguration"],
                "examples": [{"value": ","}, {"value": "|"}, {"value": ";"}],
            }
        },
    )
    reversed: Optional[bool] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {"alias": "reversed", "domain_of": ["StringificationConfiguration"]}
        },
    )
    over_slots: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {"alias": "over_slots", "domain_of": ["StringificationConfiguration"]}
        },
    )
    syntax: Optional[SerializationSyntaxType] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "syntax",
                "domain_of": ["StringificationConfiguration"],
                "examples": [{"value": "json"}, {"value": "yaml"}],
            }
        },
    )


class Inverse(ConfiguredBaseModel):
    """
    Used for back references in mapping to relational model
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "aliases": ["backref", "back_references"],
            "from_schema": "https://w3id.org/linkml/transformer",
        }
    )

    slot_name: Optional[str] = Field(
        None, json_schema_extra={"linkml_meta": {"alias": "slot_name", "domain_of": ["Inverse"]}}
    )
    class_name: Optional[str] = Field(
        None, json_schema_extra={"linkml_meta": {"alias": "class_name", "domain_of": ["Inverse"]}}
    )


class TransformationOperation(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"abstract": True, "from_schema": "https://w3id.org/linkml/transformer"}
    )

    pass


class AggregationOperation(TransformationOperation):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    operator: AggregationType = Field(
        ...,
        json_schema_extra={
            "linkml_meta": {"alias": "operator", "domain_of": ["AggregationOperation"]}
        },
    )
    null_handling: Optional[InvalidValueHandlingStrategy] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "null_handling",
                "domain_of": ["AggregationOperation", "GroupingOperation"],
            }
        },
    )
    invalid_value_handling: Optional[InvalidValueHandlingStrategy] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "invalid_value_handling",
                "domain_of": ["AggregationOperation"],
            }
        },
    )


class GroupingOperation(TransformationOperation):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    null_handling: Optional[InvalidValueHandlingStrategy] = Field(
        None,
        json_schema_extra={
            "linkml_meta": {
                "alias": "null_handling",
                "domain_of": ["AggregationOperation", "GroupingOperation"],
            }
        },
    )


class PivotOperation(TransformationOperation):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "aliases": ["melt/unmelt", "reification/dereification"],
            "from_schema": "https://w3id.org/linkml/transformer",
        }
    )

    direction: PivotDirectionType = Field(
        ...,
        json_schema_extra={"linkml_meta": {"alias": "direction", "domain_of": ["PivotOperation"]}},
    )
    variable_slot: Optional[str] = Field(
        "variable",
        description="""Slot to use for the variable column in the melted/long representation. In EAV this is the name of the 'A' variable""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "variable_slot",
                "aliases": ["var_name"],
                "domain_of": ["PivotOperation"],
                "ifabsent": "string(variable)",
            }
        },
    )
    value_slot: Optional[str] = Field(
        "value",
        description="""Slot to use for the value column in the melted/long representation. In EAV this is the name of the 'V' variable""",
        json_schema_extra={
            "linkml_meta": {
                "alias": "value_slot",
                "aliases": ["value_name"],
                "domain_of": ["PivotOperation"],
                "ifabsent": "string(value)",
            }
        },
    )
    unmelt_to_class: Optional[str] = Field(
        None,
        description="""In an unmelt operation, attributes (which are values in the long/melted/EAV representation) must conform to valid attributes in this class""",
        json_schema_extra={
            "linkml_meta": {"alias": "unmelt_to_class", "domain_of": ["PivotOperation"]}
        },
    )
    unmelt_to_slots: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "linkml_meta": {"alias": "unmelt_to_slots", "domain_of": ["PivotOperation"]}
        },
    )


class KeyVal(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer"}
    )

    key: str = Field(
        ..., json_schema_extra={"linkml_meta": {"alias": "key", "domain_of": ["KeyVal"]}}
    )
    value: Optional[Any] = Field(
        None, json_schema_extra={"linkml_meta": {"alias": "value", "domain_of": ["KeyVal"]}}
    )


class CopyDirective(ConfiguredBaseModel):
    """
    Instructs a Schema Mapper in how to map to a target schema. Not used for data transformation.
    This is the process to process a directive:
    1. If `copy_all`, add all sub-elements to the list of sub-elements to be copied.
    2. If `exclude`, remove the specified sub-elements from the above list.
    3. If `exclude_all`, clean-up the above list. Effectively making previous steps useless.
    4. If `include`, add the specified sub-elements from the list result of previous steps.
    Implementations might decide to somehow report (error, warning,...) meaningless combinations
    (like specifying `copy_all` and `exclude_all`).
    Validation on the correctness of the resulting derived schema might be done optionally by the implementation.
    For example, removing a slot but keeping a class that requires it would invalidate the derived-schema.
    It is always possible to validate the schema with the LinkML linter after derivation.
    What are the considered sub-elements depends on the calls of Element to be transformed.
    For example, for a class they are `slots` and `attributes`.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://w3id.org/linkml/transformer", "status": "testing"}
    )

    element_name: str = Field(
        ...,
        json_schema_extra={
            "linkml_meta": {"alias": "element_name", "domain_of": ["CopyDirective"]}
        },
    )
    copy_all: Optional[bool] = Field(
        None,
        description="""Copy all sub-elements of the Element being derived.""",
        json_schema_extra={"linkml_meta": {"alias": "copy_all", "domain_of": ["CopyDirective"]}},
    )
    exclude_all: Optional[bool] = Field(
        None,
        description="""Do not copy any of the sub-elements of the Element being derived.""",
        json_schema_extra={"linkml_meta": {"alias": "exclude_all", "domain_of": ["CopyDirective"]}},
    )
    exclude: Optional[Any] = Field(
        None,
        description="""Remove certain sub-elements from the list of sub-elements to be copied.
As of now there it is under-specified, how to specify the sub-elements to exclude. One possible implementation would be a list where all element types can be mixed, since there might not be name conflicts across element types.""",
        json_schema_extra={"linkml_meta": {"alias": "exclude", "domain_of": ["CopyDirective"]}},
    )
    include: Optional[Any] = Field(
        None,
        description="""Add certain sub-elements to the list of sub-elements to be copied.
As of now there it is under-specified, how to specify the sub-elements to include. One possible implementation would be a list where all element types can be mixed, since there might not be name conflicts across element types.""",
        json_schema_extra={"linkml_meta": {"alias": "include", "domain_of": ["CopyDirective"]}},
    )
    add: Optional[Any] = Field(
        None, json_schema_extra={"linkml_meta": {"alias": "add", "domain_of": ["CopyDirective"]}}
    )


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
SpecificationComponent.model_rebuild()
TransformationSpecification.model_rebuild()
ElementDerivation.model_rebuild()
ClassDerivation.model_rebuild()
AliasedClass.model_rebuild()
SlotDerivation.model_rebuild()
EnumDerivation.model_rebuild()
PermissibleValueDerivation.model_rebuild()
PrefixDerivation.model_rebuild()
UnitConversionConfiguration.model_rebuild()
StringificationConfiguration.model_rebuild()
Inverse.model_rebuild()
TransformationOperation.model_rebuild()
AggregationOperation.model_rebuild()
GroupingOperation.model_rebuild()
PivotOperation.model_rebuild()
KeyVal.model_rebuild()
CopyDirective.model_rebuild()
