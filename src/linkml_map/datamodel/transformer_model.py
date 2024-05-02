from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic.version import VERSION as PYDANTIC_VERSION

if int(PYDANTIC_VERSION[0]) >= 2:
    from pydantic import BaseModel, ConfigDict, Field
else:
    from pydantic import BaseModel, Field

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


class CollectionType(str, Enum):
    SingleValued = "SingleValued"
    MultiValued = "MultiValued"
    MultiValuedList = "MultiValuedList"
    MultiValuedDict = "MultiValuedDict"


class SerializationSyntaxType(str, Enum):
    JSON = "JSON"
    YAML = "YAML"
    TURTLE = "TURTLE"


class SpecificationComponent(ConfiguredBaseModel):
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class TransformationSpecification(SpecificationComponent):
    """
    A collection of mappings between source and target classes
    """

    id: Optional[str] = Field(
        None, description="""Unique identifier for this transformation specification"""
    )
    title: Optional[str] = Field(
        None, description="""human readable title for this transformation specification"""
    )
    prefixes: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict, description="""maps prefixes to URL expansions"""
    )
    source_schema: Optional[str] = Field(
        None, description="""name of the schema that describes the source (input) objects"""
    )
    target_schema: Optional[str] = Field(
        None, description="""name of the schema that describes the target (output) objects"""
    )
    class_derivations: Optional[Dict[str, ClassDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of classes in the target schema from classes in the source schema.""",
    )
    enum_derivations: Optional[Dict[str, EnumDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of enums in the target schema""",
    )
    slot_derivations: Optional[Dict[str, SlotDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of top level slots in the target schema""",
    )
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class ElementDerivation(SpecificationComponent):
    """
    An abstract grouping for classes that provide a specification of how to  derive a target element from a source element.
    """

    name: str = Field(..., description="""Name of the element in the target schema""")
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(default_factory=dict)
    overrides: Optional[Any] = Field(None, description="""overrides source schema slots""")
    is_a: Optional[str] = Field(None)
    mixins: Optional[List[str]] = Field(default_factory=list)
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict, description="""A mapping table in which the keys are expressions"""
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
    )
    mirror_source: Optional[bool] = Field(None)
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class ClassDerivation(ElementDerivation):
    """
    A specification of how to derive a target class from a source class.
    """

    populated_from: Optional[str] = Field(
        None, description="""Name of the class in the source schema"""
    )
    sources: Optional[List[str]] = Field(default_factory=list)
    joins: Optional[Dict[str, AliasedClass]] = Field(
        default_factory=dict,
        description="""Additional classes to be joined to derive instances of the target class""",
    )
    slot_derivations: Optional[Dict[str, SlotDerivation]] = Field(default_factory=dict)
    name: str = Field(..., description="""Name of the element in the target schema""")
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(default_factory=dict)
    overrides: Optional[Any] = Field(None, description="""overrides source schema slots""")
    is_a: Optional[str] = Field(None)
    mixins: Optional[List[str]] = Field(default_factory=list)
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict, description="""A mapping table in which the keys are expressions"""
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
    )
    mirror_source: Optional[bool] = Field(None)
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class AliasedClass(ConfiguredBaseModel):
    """
    alias-class key value pairs for classes
    """

    alias: str = Field(..., description="""name of the class to be aliased""")
    class_named: Optional[str] = Field(None, description="""local alias for the class""")


class SlotDerivation(ElementDerivation):
    """
    A specification of how to derive the value of a target slot from a source slot
    """

    name: str = Field(..., description="""Target slot name""")
    populated_from: Optional[str] = Field(None, description="""Source slot name""")
    sources: Optional[List[str]] = Field(default_factory=list)
    derived_from: Optional[List[str]] = Field(
        default_factory=list,
        description="""Source slots that are used to derive this slot. This can be computed from the expr, if the expr is declarative.""",
    )
    expr: Optional[str] = Field(
        None,
        description="""An expression to be evaluated on the source object to derive the target slot. Should be specified using the LinkML expression language.""",
    )
    range: Optional[str] = Field(None)
    unit_conversion: Optional[UnitConversionConfiguration] = Field(None)
    inverse_of: Optional[Inverse] = Field(
        None,
        description="""Used to specify a class-slot tuple that is the inverse of the derived/target slot. This is used primarily for mapping to relational databases or formalisms that do not allow multiple values. The class representing the repeated element has a foreign key slot inserted in that 'back references' the original multivalued slot.""",
    )
    hide: Optional[bool] = Field(None, description="""True if this is suppressed""")
    type_designator: Optional[bool] = Field(None)
    cast_collection_as: Optional[CollectionType] = Field(None)
    dictionary_key: Optional[str] = Field(None)
    stringification: Optional[StringificationConfiguration] = Field(None)
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(default_factory=dict)
    overrides: Optional[Any] = Field(None, description="""overrides source schema slots""")
    is_a: Optional[str] = Field(None)
    mixins: Optional[List[str]] = Field(default_factory=list)
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict, description="""A mapping table in which the keys are expressions"""
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
    )
    mirror_source: Optional[bool] = Field(None)
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class EnumDerivation(ElementDerivation):
    """
    A specification of how to derive the value of a target enum from a source enum
    """

    name: str = Field(..., description="""Target enum name""")
    populated_from: Optional[str] = Field(None, description="""Source enum name""")
    sources: Optional[List[str]] = Field(default_factory=list)
    expr: Optional[str] = Field(
        None,
        description="""An expression to be evaluated on the source object to derive the target slot. Should be specified using the LinkML expression language.""",
    )
    hide: Optional[bool] = Field(None, description="""True if this is suppressed""")
    permissible_value_derivations: Optional[Dict[str, PermissibleValueDerivation]] = Field(
        default_factory=dict,
        description="""Instructions on how to derive a set of PVs in the target schema""",
    )
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(default_factory=dict)
    overrides: Optional[Any] = Field(None, description="""overrides source schema slots""")
    is_a: Optional[str] = Field(None)
    mixins: Optional[List[str]] = Field(default_factory=list)
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict, description="""A mapping table in which the keys are expressions"""
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
    )
    mirror_source: Optional[bool] = Field(None)
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class PermissibleValueDerivation(ElementDerivation):
    """
    A specification of how to derive the value of a PV from a source enum
    """

    name: str = Field(..., description="""Target permissible value text""")
    expr: Optional[str] = Field(None)
    populated_from: Optional[str] = Field(None, description="""Source permissible value""")
    sources: Optional[List[str]] = Field(default_factory=list)
    hide: Optional[bool] = Field(None)
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(default_factory=dict)
    overrides: Optional[Any] = Field(None, description="""overrides source schema slots""")
    is_a: Optional[str] = Field(None)
    mixins: Optional[List[str]] = Field(default_factory=list)
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict, description="""A mapping table in which the keys are expressions"""
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
    )
    mirror_source: Optional[bool] = Field(None)
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class PrefixDerivation(ElementDerivation):
    name: str = Field(..., description="""Name of the element in the target schema""")
    copy_directives: Optional[Dict[str, CopyDirective]] = Field(default_factory=dict)
    overrides: Optional[Any] = Field(None, description="""overrides source schema slots""")
    is_a: Optional[str] = Field(None)
    mixins: Optional[List[str]] = Field(default_factory=list)
    value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table that is applied directly to mappings, in order of precedence""",
    )
    expression_to_value_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict, description="""A mapping table in which the keys are expressions"""
    )
    expression_to_expression_mappings: Optional[Dict[str, KeyVal]] = Field(
        default_factory=dict,
        description="""A mapping table in which the keys and values are expressions""",
    )
    mirror_source: Optional[bool] = Field(None)
    description: Optional[str] = Field(
        None, description="""description of the specification component"""
    )
    implements: Optional[List[str]] = Field(
        default_factory=list,
        description="""A reference to a specification that this component implements.""",
    )
    comments: Optional[List[str]] = Field(
        default_factory=list,
        description="""A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use.""",
    )


class UnitConversionConfiguration(ConfiguredBaseModel):
    target_unit: Optional[str] = Field(None)
    target_unit_scheme: Optional[str] = Field(None)
    source_unit: Optional[str] = Field(None)
    source_unit_scheme: Optional[str] = Field(None)
    source_unit_slot: Optional[str] = Field(None)
    source_magnitude_slot: Optional[str] = Field(None)
    target_unit_slot: Optional[str] = Field(None)
    target_magnitude_slot: Optional[str] = Field(None)


class StringificationConfiguration(ConfiguredBaseModel):
    delimiter: Optional[str] = Field(None)
    reversed: Optional[bool] = Field(None)
    over_slots: Optional[List[str]] = Field(default_factory=list)
    syntax: Optional[SerializationSyntaxType] = Field(None)


class Inverse(ConfiguredBaseModel):
    """
    Used for back references in mapping to relational model
    """

    slot_name: Optional[str] = Field(None)
    class_name: Optional[str] = Field(None)


class KeyVal(ConfiguredBaseModel):
    key: str = Field(...)
    value: Optional[Any] = Field(None)


class CopyDirective(ConfiguredBaseModel):
    """
    Instructs a Schema Mapper in how to map to a target schema. Not used for data transformation.
    """

    element_name: str = Field(...)
    copy_all: Optional[bool] = Field(None)
    exclude_all: Optional[bool] = Field(None)
    exclude: Optional[Any] = Field(None)
    include: Optional[Any] = Field(None)
    add: Optional[Any] = Field(None)


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
KeyVal.model_rebuild()
CopyDirective.model_rebuild()
