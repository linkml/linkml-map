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
| [Any](Any.md) |  |
| [CopyDirective](CopyDirective.md) | Instructs a Schema Mapper in how to map to a target schema |
| [Inverse](Inverse.md) | Used for back references in mapping to relational model |
| [KeyVal](KeyVal.md) |  |
| [Offset](Offset.md) | Configuration for calculating a value by applying an offset to a baseline val... |
| [SchemaReference](SchemaReference.md) | A reference to a LinkML schema, with optional version and locator metadata |
| [SpecificationComponent](SpecificationComponent.md) |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ElementDerivation](ElementDerivation.md) | An abstract grouping for classes that provide a specification of how to deriv... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ClassDerivation](ClassDerivation.md) | A specification of how to derive a target class from a source class |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[EnumDerivation](EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enu... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ObjectDerivation](ObjectDerivation.md) | Deprecated |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PermissibleValueDerivation](PermissibleValueDerivation.md) | A specification of how to derive the value of a PV from a source enum |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PrefixDerivation](PrefixDerivation.md) |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |
| [StringificationConfiguration](StringificationConfiguration.md) |  |
| [TransformationOperation](TransformationOperation.md) |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[AggregationOperation](AggregationOperation.md) |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[GroupingOperation](GroupingOperation.md) |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PivotOperation](PivotOperation.md) |  |
| [UnitConversionConfiguration](UnitConversionConfiguration.md) |  |



## Slots

| Slot | Description |
| --- | --- |
| [add](add.md) |  |
| [affiliation](affiliation.md) | Institutional affiliation of the person |
| [aggregation_operation](aggregation_operation.md) |  |
| [alias](alias.md) | name of the class to be aliased |
| [author](author.md) | A list of authors of this transformation specification |
| [cast_collection_as](cast_collection_as.md) |  |
| [class_derivations](class_derivations.md) | Instructions on how to derive a set of classes in the target schema from clas... |
| [class_name](class_name.md) |  |
| [class_named](class_named.md) | local alias for the class |
| [comments](comments.md) | A list of comments about this component |
| [content_url](content_url.md) | Reference to the actual content of the mapping specification |
| [copy_all](copy_all.md) | Copy all sub-elements of the Element being derived |
| [copy_directives](copy_directives.md) |  |
| [creator](creator.md) | A list of creators of this transformation specification |
| [delimiter](delimiter.md) |  |
| [derived_from](derived_from.md) | Deprecated |
| [description](description.md) | description of the specification component |
| [dictionary_key](dictionary_key.md) |  |
| [direction](direction.md) |  |
| [documentation](documentation.md) | URL or reference to documentation for the mapping specification |
| [element_name](element_name.md) |  |
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
| [invalid_value_handling](invalid_value_handling.md) |  |
| [inverse_of](inverse_of.md) | Used to specify a class-slot tuple that is the inverse of the derived/target ... |
| [is_a](is_a.md) |  |
| [join_on](join_on.md) | shorthand for source_key and lookup_key when both share the same column name |
| [joins](joins.md) | Additional classes to be joined to derive instances of the target class |
| [key](key.md) |  |
| [license](license.md) | license under which this transformation specification is published |
| [lookup_key](lookup_key.md) | column in the secondary (joined) table used as the join key |
| [mapping_method](mapping_method.md) | The method used to create this mapping, e |
| [mirror_source](mirror_source.md) |  |
| [mixins](mixins.md) |  |
| [name](name.md) | The name or identifier of the schema |
| [none_if_non_numeric](none_if_non_numeric.md) | If true, return None when the source value cannot be coerced to a numeric typ... |
| [null_handling](null_handling.md) |  |
| [object_derivations](object_derivations.md) | Deprecated |
| [offset](offset.md) | Configuration for calculating a value by applying an offset to a baseline val... |
| [offset_field](offset_field.md) | Name of the field in the source object that contains the offset amount |
| [offset_reverse](offset_reverse.md) | If true, subtract the offset from the baseline (baseline - offset) |
| [offset_value](offset_value.md) | Multiplier applied to the offset field value |
| [operator](operator.md) |  |
| [orcid](orcid.md) | ORCID identifier for the person |
| [over_slots](over_slots.md) |  |
| [overrides](overrides.md) | overrides source schema slots |
| [permissible_value_derivations](permissible_value_derivations.md) | Instructions on how to derive a set of PVs in the target schema |
| [pivot_operation](pivot_operation.md) | Configuration for pivot (unmelt) operations at class level |
| [populated_from](populated_from.md) | Source class to derive this target class from |
| [prefixes](prefixes.md) | maps prefixes to URL expansions |
| [publication_date](publication_date.md) | date of publication of this transformation specification |
| [range](range.md) |  |
| [repository_url](repository_url.md) | URL to a code repository |
| [reversed](reversed.md) |  |
| [reviewer](reviewer.md) | A list of reviewers of this transformation specification |
| [ror_id](ror_id.md) | ROR (Research Organization Registry) identifier |
| [schema_uri](schema_uri.md) | The URI/IRI identifier of the schema (matches the schema's `id`) |
| [slot_derivations](slot_derivations.md) | Instructions on how to derive a set of top level slots in the target schema |
| [slot_name](slot_name.md) |  |
| [slot_name_template](slot_name_template.md) | Template for generating target slot names |
| [source_file](source_file.md) | Optional file path or URL from which the schema can be loaded |
| [source_key](source_key.md) | column in the primary (populated_from) table used as the join key |
| [source_magnitude_slot](source_magnitude_slot.md) |  |
| [source_schema](source_schema.md) | Reference to the schema that describes the source (input) objects |
| [source_schema_patches](source_schema_patches.md) | Schema patches to apply to the source schema before transformation |
| [source_slots](source_slots.md) | For MELT, the list of wide-format slots to melt |
| [source_unit](source_unit.md) |  |
| [source_unit_scheme](source_unit_scheme.md) |  |
| [source_unit_slot](source_unit_slot.md) |  |
| [sources](sources.md) | Deprecated |
| [stringification](stringification.md) |  |
| [syntax](syntax.md) |  |
| [target_definition](target_definition.md) | LinkML class definition object for this slot |
| [target_magnitude_slot](target_magnitude_slot.md) |  |
| [target_schema](target_schema.md) | Reference to the schema that describes the target (output) objects |
| [target_unit](target_unit.md) |  |
| [target_unit_scheme](target_unit_scheme.md) |  |
| [target_unit_slot](target_unit_slot.md) |  |
| [title](title.md) | human readable title for this transformation specification |
| [type](type.md) | Type of the agent |
| [type_designator](type_designator.md) |  |
| [unit_conversion](unit_conversion.md) |  |
| [unit_slot](unit_slot.md) | Optional slot containing unit information for {variable}_{unit} naming |
| [unmelt_to_class](unmelt_to_class.md) | In an unmelt operation, attributes (which are values in the long/melted/EAV r... |
| [unmelt_to_slots](unmelt_to_slots.md) |  |
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
