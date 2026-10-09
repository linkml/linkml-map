---
search:
  boost: 5.0
---

# Slot: class_defaults 


_Settings for every class derivation whose target is the named class, unless the derivation sets its own._



<div data-search-exclude markdown="1">



URI: [linkmlmap:class_defaults](https://w3id.org/linkml/transformer/class_defaults)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ClassDefault](ClassDefault.md) |
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
| self | linkmlmap:class_defaults |
| native | linkmlmap:class_defaults |




## LinkML Source

<details>
```yaml
name: class_defaults
description: Settings for every class derivation whose target is the named class,
  unless the derivation sets its own.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: TransformationSpecification
domain_of:
- TransformationSpecification
range: ClassDefault
multivalued: true
inlined: true

```
</details></div>