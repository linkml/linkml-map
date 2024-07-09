# LinkML Map Data Model

Datamodel for LinkML schema mappings and transformations.

A mapper generates instances of a *target* data model from
instances of a *source* data model. This transformation process
is guided by a *TransformationSpecification*.

The specification is independent of any one method for transforming
data. It allows different approaches, including:

- direct implementation, transforming python or json objects
- translation of the specification into SQL commands, to operate on relations
- translation of the specification into SPARQL CONSTRUCTs, to operate on triples
- translation into another specification language, such as R2RML

URI: https://w3id.org/linkml/transformer

Name: linkml-map



## Classes

| Class | Description |
| --- | --- |
| [AliasedClass](AliasedClass.md) | alias-class key value pairs for classes |
| [Any](Any.md) | None |
| [CopyDirective](CopyDirective.md) | Instructs a Schema Mapper in how to map to a target schema. Not used for data transformation. |
| [Inverse](Inverse.md) | Used for back references in mapping to relational model |
| [KeyVal](KeyVal.md) | None |
| [SpecificationComponent](SpecificationComponent.md) | None |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ElementDerivation](ElementDerivation.md) | An abstract grouping for classes that provide a specification of how to  derive a target element from a source element. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ClassDerivation](ClassDerivation.md) | A specification of how to derive a target class from a source class. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[EnumDerivation](EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enum |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PermissibleValueDerivation](PermissibleValueDerivation.md) | A specification of how to derive the value of a PV from a source enum |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PrefixDerivation](PrefixDerivation.md) | None |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slot |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |
| [StringificationConfiguration](StringificationConfiguration.md) | None |
| [UnitConversionConfiguration](UnitConversionConfiguration.md) | None |



## Slots

| Slot | Description |
| --- | --- |
| [add](add.md) |  |
| [alias](alias.md) | name of the class to be aliased |
| [cast_collection_as](cast_collection_as.md) |  |
| [class_derivations](class_derivations.md) | Instructions on how to derive a set of classes in the target schema from clas... |
| [class_name](class_name.md) |  |
| [class_named](class_named.md) | local alias for the class |
| [comments](comments.md) | A list of comments about this component |
| [copy_all](copy_all.md) |  |
| [copy_directives](copy_directives.md) |  |
| [delimiter](delimiter.md) |  |
| [derived_from](derived_from.md) | Source slots that are used to derive this slot |
| [description](description.md) | description of the specification component |
| [dictionary_key](dictionary_key.md) |  |
| [element_name](element_name.md) |  |
| [enum_derivations](enum_derivations.md) | Instructions on how to derive a set of enums in the target schema |
| [exclude](exclude.md) |  |
| [exclude_all](exclude_all.md) |  |
| [expr](expr.md) | An expression to be evaluated on the source object to derive the target slot |
| [expression_to_expression_mappings](expression_to_expression_mappings.md) | A mapping table in which the keys and values are expressions |
| [expression_to_value_mappings](expression_to_value_mappings.md) | A mapping table in which the keys are expressions |
| [hide](hide.md) | True if this is suppressed |
| [id](id.md) | Unique identifier for this transformation specification |
| [implements](implements.md) | A reference to a specification that this component implements |
| [include](include.md) |  |
| [inverse_of](inverse_of.md) | Used to specify a class-slot tuple that is the inverse of the derived/target ... |
| [is_a](is_a.md) |  |
| [joins](joins.md) | Additional classes to be joined to derive instances of the target class |
| [key](key.md) |  |
| [mirror_source](mirror_source.md) |  |
| [mixins](mixins.md) |  |
| [name](name.md) | Name of the element in the target schema |
| [over_slots](over_slots.md) |  |
| [overrides](overrides.md) | overrides source schema slots |
| [permissible_value_derivations](permissible_value_derivations.md) | Instructions on how to derive a set of PVs in the target schema |
| [populated_from](populated_from.md) | Name of the class in the source schema |
| [prefixes](prefixes.md) | maps prefixes to URL expansions |
| [range](range.md) |  |
| [reversed](reversed.md) |  |
| [slot_derivations](slot_derivations.md) | Instructions on how to derive a set of top level slots in the target schema |
| [slot_name](slot_name.md) |  |
| [source_magnitude_slot](source_magnitude_slot.md) |  |
| [source_schema](source_schema.md) | name of the schema that describes the source (input) objects |
| [source_unit](source_unit.md) |  |
| [source_unit_scheme](source_unit_scheme.md) |  |
| [source_unit_slot](source_unit_slot.md) |  |
| [sources](sources.md) |  |
| [stringification](stringification.md) |  |
| [syntax](syntax.md) |  |
| [target_magnitude_slot](target_magnitude_slot.md) |  |
| [target_schema](target_schema.md) | name of the schema that describes the target (output) objects |
| [target_unit](target_unit.md) |  |
| [target_unit_scheme](target_unit_scheme.md) |  |
| [target_unit_slot](target_unit_slot.md) |  |
| [title](title.md) | human readable title for this transformation specification |
| [type_designator](type_designator.md) |  |
| [unit_conversion](unit_conversion.md) |  |
| [value](value.md) |  |
| [value_mappings](value_mappings.md) | A mapping table that is applied directly to mappings, in order of precedence |


## Enumerations

| Enumeration | Description |
| --- | --- |
| [CollectionType](CollectionType.md) |  |
| [SerializationSyntaxType](SerializationSyntaxType.md) |  |


## Types

| Type | Description |
| --- | --- |
| [Boolean](Boolean.md) | A binary (true or false) value |
| [ClassReference](ClassReference.md) |  |
| [Curie](Curie.md) | a compact URI |
| [Date](Date.md) | a date (year, month and day) in an idealized calendar |
| [DateOrDatetime](DateOrDatetime.md) | Either a date or a datetime |
| [Datetime](Datetime.md) | The combination of a date and time |
| [Decimal](Decimal.md) | A real number with arbitrary precision that conforms to the xsd:decimal speci... |
| [Double](Double.md) | A real number that conforms to the xsd:double specification |
| [EnumReference](EnumReference.md) |  |
| [Float](Float.md) | A real number that conforms to the xsd:float specification |
| [Integer](Integer.md) | An integer |
| [Jsonpath](Jsonpath.md) | A string encoding a JSON Path |
| [Jsonpointer](Jsonpointer.md) | A string encoding a JSON Pointer |
| [Ncname](Ncname.md) | Prefix part of CURIE |
| [Nodeidentifier](Nodeidentifier.md) | A URI, CURIE or BNODE that represents a node in a model |
| [Objectidentifier](Objectidentifier.md) | A URI or CURIE that represents an object in the model |
| [SlotReference](SlotReference.md) |  |
| [Sparqlpath](Sparqlpath.md) | A string encoding a SPARQL Property Path |
| [String](String.md) | A character string |
| [Time](Time.md) | A time object represents a (local) time of day, independent of any particular... |
| [Uri](Uri.md) | a complete URI |
| [Uriorcurie](Uriorcurie.md) | a URI or a CURIE |


## Subsets

| Subset | Description |
| --- | --- |
