---
search:
  boost: 5.0
---

# Slot: prefixes 


_maps prefixes to URL expansions_



<div data-search-exclude markdown="1">



URI: [sh:declare](http://www.w3.org/ns/shacl#declare)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [KeyVal](KeyVal.md) |
| Domain Of | [TransformationSpecification](TransformationSpecification.md) |
| Slot URI | [sh:declare](http://www.w3.org/ns/shacl#declare) |

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
| self | sh:declare |
| native | linkmlmap:prefixes |




## LinkML Source

<details>
```yaml
name: prefixes
description: maps prefixes to URL expansions
from_schema: https://w3id.org/linkml/transformer
rank: 1000
slot_uri: sh:declare
owner: TransformationSpecification
domain_of:
- TransformationSpecification
range: KeyVal
multivalued: true
inlined: true

```
</details></div>