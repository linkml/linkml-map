---
search:
  boost: 5.0
---

# Slot: source_schema 


_Reference to the schema that describes the source (input) objects._



<div data-search-exclude markdown="1">



URI: [linkmlmap:source_schema](https://w3id.org/linkml/transformer/source_schema)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [SchemaReference](SchemaReference.md) |
| Domain Of | [TransformationSpecification](TransformationSpecification.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [TransformationSpecification](TransformationSpecification.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:source_schema |
| native | linkmlmap:source_schema |




## LinkML Source

<details>
```yaml
name: source_schema
description: Reference to the schema that describes the source (input) objects.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: TransformationSpecification
domain_of:
- TransformationSpecification
range: SchemaReference
inlined: true

```
</details></div>