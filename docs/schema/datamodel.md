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
| [Agent](Agent.md) | An entity that can create or contribute to a digital object, such as an autho... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Organization](Organization.md) | An organization or institution that contributes to a mapping specification |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Person](Person.md) | An individual person who contributes to a mapping specification |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Software](Software.md) | A software tool or system used in creating mappings |
| [AliasedClass](AliasedClass.md) | alias-class key value pairs for classes |
| [Any](Any.md) | A wildcard type that accepts any value |
| [CopyDirective](CopyDirective.md) | Instructs a Schema Mapper in how to map to a target schema |
| [Inverse](Inverse.md) | Used for back references in mapping to relational model |
| [KeyVal](KeyVal.md) | A generic key-value pair |
| [Offset](Offset.md) | Configuration for calculating a value by applying an offset to a baseline val... |
| [SchemaReference](SchemaReference.md) | A reference to a LinkML schema, with optional version and locator metadata |
| [SpecificationComponent](SpecificationComponent.md) |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ElementDerivation](ElementDerivation.md) | An abstract grouping for classes that provide a specification of how to deriv... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ClassDerivation](ClassDerivation.md) | A specification of how to derive a target class from a source class |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[EnumDerivation](EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enu... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ObjectDerivation](ObjectDerivation.md) | Deprecated |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PermissibleValueDerivation](PermissibleValueDerivation.md) | A specification of how to derive the value of a PV from a source enum |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PrefixDerivation](PrefixDerivation.md) | A specification of how to derive a target prefix declaration |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |
| [StringificationConfiguration](StringificationConfiguration.md) | Configuration for collapsing multiple values into a single delimited or seria... |
| [TransformationOperation](TransformationOperation.md) |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[AggregationOperation](AggregationOperation.md) | An operation that reduces multiple input values to a single value using an ag... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[GroupingOperation](GroupingOperation.md) | An operation that groups source rows prior to aggregation |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PivotOperation](PivotOperation.md) | An operation that reshapes data between wide and long (EAV) representations, ... |
| [UnitConversionConfiguration](UnitConversionConfiguration.md) | Configuration for converting a slot value from a source unit of measure to a ... |



## Slots

| Slot | Description |
| --- | --- |
| [add](add.md) | Add new sub-elements that are not present in the source element |
| [affiliation](affiliation.md) | Institutional affiliation of the person |
| [aggregation_operation](aggregation_operation.md) | An aggregation operation that reduces multiple source values into this slot's... |
| [alias](alias.md) | name of the class to be aliased |
| [author](author.md) | A list of authors of this transformation specification |
| [cast_collection_as](cast_collection_as.md) | Coerce the derived slot's collection form (for example single-valued, list, o... |
| [class_derivations](class_derivations.md) | Instructions on how to derive a set of classes in the target schema from clas... |
| [class_name](class_name.md) | Name of the class that holds the back-reference (foreign key) slot |
| [class_named](class_named.md) | local alias for the class |
| [comments](comments.md) | A list of comments about this component |
| [content_url](content_url.md) | Reference to the actual content of the mapping specification |
| [copy_all](copy_all.md) | Copy all sub-elements of the Element being derived |
| [copy_directives](copy_directives.md) | Directives controlling which elements of the source schema are copied into th... |
| [creator](creator.md) | A list of creators of this transformation specification |
| [delimiter](delimiter.md) | Delimiter used to join multiple values into a single string |
| [derived_from](derived_from.md) | Deprecated |
| [description](description.md) | description of the specification component |
| [dictionary_key](dictionary_key.md) | When the derived value is a list of objects, the slot whose value is used as ... |
| [direction](direction.md) | Whether to MELT (wide to long) or UNMELT (long to wide) |
| [documentation](documentation.md) | URL or reference to documentation for the mapping specification |
| [element_name](element_name.md) | Name of the source element this directive applies to (a class, slot, enum, et... |
| [enum_derivations](enum_derivations.md) | Instructions on how to derive a set of enums in the target schema |
| [exclude](exclude.md) | Remove certain sub-elements from the list of sub-elements to be copied |
| [exclude_all](exclude_all.md) | Do not copy any of the sub-elements of the Element being derived |
| [expr](expr.md) | An expression to be evaluated on the source object to derive the target slot |
| [expression_mappings](expression_mappings.md) | A mapping table where the values are expressions evaluated against source bin... |
| [expression_to_expression_mappings](expression_to_expression_mappings.md) | A mapping table in which the keys and values are expressions |
| [expression_to_value_mappings](expression_to_value_mappings.md) | A mapping table in which the keys are boolean expressions and the values are ... |
| [hide](hide.md) | True if this is suppressed |
| [id](id.md) | Unique identifier for this transformation specification |
| [id_slots](id_slots.md) | Slots that identify the entity (not pivoted) |
| [implements](implements.md) | A reference to a specification that this component implements |
| [include](include.md) | Add certain sub-elements to the list of sub-elements to be copied |
| [invalid_value_handling](invalid_value_handling.md) | How to handle values that cannot be interpreted as valid input to the aggrega... |
| [inverse_of](inverse_of.md) | Used to specify a class-slot tuple that is the inverse of the derived/target ... |
| [is_a](is_a.md) | The parent element that the derived target element inherits from |
| [join_on](join_on.md) | shorthand for source_key and lookup_key when both share the same column name |
| [joins](joins.md) | Additional classes to be joined to derive instances of the target class |
| [key](key.md) | The key |
| [license](license.md) | license under which this transformation specification is published |
| [lookup_key](lookup_key.md) | column in the secondary (joined) table used as the join key |
| [mapping_method](mapping_method.md) | The method used to create this mapping, e |
| [mirror_source](mirror_source.md) | If true, pass the source value through unchanged instead of transforming it |
| [missing_values](missing_values.md) | Source values that represent a missing observation and should be emitted as n... |
| [mixins](mixins.md) | Mixin elements applied to the derived target element |
| [name](name.md) | The name or identifier of the schema |
| [none_if_non_numeric](none_if_non_numeric.md) | If true, return None when the source value cannot be coerced to a numeric typ... |
| [null_handling](null_handling.md) | How to handle null values encountered during aggregation |
| [object_derivations](object_derivations.md) | Deprecated |
| [offset](offset.md) | Configuration for calculating a value by applying an offset to a baseline val... |
| [offset_field](offset_field.md) | Name of the field in the source object that contains the offset amount |
| [offset_reverse](offset_reverse.md) | If true, subtract the offset from the baseline (baseline - offset) |
| [offset_value](offset_value.md) | Multiplier applied to the offset field value |
| [operator](operator.md) | The aggregation function to apply (for example SUM, AVERAGE, COUNT) |
| [orcid](orcid.md) | ORCID identifier for the person |
| [over_slots](over_slots.md) | The source slots whose values are combined into the stringified result |
| [overrides](overrides.md) | overrides source schema slots |
| [permissible_value_derivations](permissible_value_derivations.md) | Instructions on how to derive a set of PVs in the target schema |
| [pivot_operation](pivot_operation.md) | Configuration for pivot (unmelt) operations at class level |
| [populated_from](populated_from.md) | Source class to derive this target class from |
| [prefixes](prefixes.md) | maps prefixes to URL expansions |
| [publication_date](publication_date.md) | date of publication of this transformation specification |
| [range](range.md) | The range (value type) to assign to the derived target slot, overriding the r... |
| [repository_url](repository_url.md) | URL to a code repository |
| [reversed](reversed.md) | If true, reverse the operation, splitting a delimited or serialized string ba... |
| [reviewer](reviewer.md) | A list of reviewers of this transformation specification |
| [ror_id](ror_id.md) | ROR (Research Organization Registry) identifier |
| [schema_uri](schema_uri.md) | The URI/IRI identifier of the schema (matches the schema's `id`) |
| [slot_derivations](slot_derivations.md) | Instructions on how to derive a set of top level slots in the target schema |
| [slot_name](slot_name.md) | Name of the slot on the referenced class that back-references the derived slo... |
| [slot_name_template](slot_name_template.md) | Template for generating target slot names |
| [source_file](source_file.md) | Optional file path or URL from which the schema can be loaded |
| [source_key](source_key.md) | column in the primary (populated_from) table used as the join key |
| [source_magnitude_slot](source_magnitude_slot.md) | For structured value-and-unit source input, the key within the source value t... |
| [source_schema](source_schema.md) | Reference to the schema that describes the source (input) objects |
| [source_schema_patches](source_schema_patches.md) | Schema patches to apply to the source schema before transformation |
| [source_slots](source_slots.md) | For MELT, the list of wide-format slots to melt |
| [source_unit](source_unit.md) | The unit the source value is expressed in |
| [source_unit_scheme](source_unit_scheme.md) | The unit scheme or system identifying source_unit (for example ucum) |
| [source_unit_slot](source_unit_slot.md) | For structured value-and-unit source input, the key within the source value t... |
| [sources](sources.md) | Deprecated |
| [stringification](stringification.md) | Configuration for combining multiple values into a single string value |
| [syntax](syntax.md) | Serialization syntax used to stringify the values when no delimiter is given |
| [target_definition](target_definition.md) | LinkML class definition object for this slot |
| [target_magnitude_slot](target_magnitude_slot.md) | When emitting structured output, the key to write the converted magnitude int... |
| [target_schema](target_schema.md) | Reference to the schema that describes the target (output) objects |
| [target_unit](target_unit.md) | The unit to convert the value into |
| [target_unit_scheme](target_unit_scheme.md) | The unit scheme or system identifying target_unit (for example ucum) |
| [target_unit_slot](target_unit_slot.md) | When emitting structured output, the key to write the target unit into |
| [title](title.md) | human readable title for this transformation specification |
| [type](type.md) | Type of the agent |
| [type_designator](type_designator.md) | True if this target slot designates the type (class) of the instance, analogo... |
| [unit_conversion](unit_conversion.md) | Configuration for converting the source value's unit of measure when deriving... |
| [unit_slot](unit_slot.md) | Optional slot containing unit information for {variable}_{unit} naming |
| [unmelt_to_class](unmelt_to_class.md) | In an unmelt operation, attributes (which are values in the long/melted/EAV r... |
| [unmelt_to_slots](unmelt_to_slots.md) | For an unmelt operation, the target wide-format slots to populate from the lo... |
| [url](url.md) | URL or web address of the organization |
| [value](value.md) | A constant value to assign to the target slot |
| [value_mappings](value_mappings.md) | A mapping table that is applied directly to mappings, in order of precedence |
| [value_slot](value_slot.md) | Slot to use for the value column in the melted/long representation |
| [variable_slot](variable_slot.md) | Slot to use for the variable column in the melted/long representation |
| [version](version.md) | version of this transformation specification |


## Enumerations

| Enumeration | Description |
| --- | --- |
| [AggregationType](AggregationType.md) |  |
| [CollectionType](CollectionType.md) |  |
| [InvalidValueHandlingStrategy](InvalidValueHandlingStrategy.md) |  |
| [PivotDirectionType](PivotDirectionType.md) |  |
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
