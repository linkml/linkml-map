---
search:
  boost: 5.0
---

# Slot: enum_derivations 


_Instructions on how to derive a set of enums in the target schema_



<div data-search-exclude markdown="1">



URI: [linkmlmap:enum_derivations](https://w3id.org/linkml/transformer/enum_derivations)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [EnumDerivation](EnumDerivation.md) |
| Domain Of | [TransformationSpecification](TransformationSpecification.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
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
| self | linkmlmap:enum_derivations |
| native | linkmlmap:enum_derivations |




## LinkML Source

<details>
```yaml
name: enum_derivations
description: Instructions on how to derive a set of enums in the target schema
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: TransformationSpecification
domain_of:
- TransformationSpecification
range: EnumDerivation
multivalued: true
inlined: true

```
</details></div>