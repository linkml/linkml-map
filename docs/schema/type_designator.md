---
search:
  boost: 5.0
---

# Slot: type_designator 


_True if this target slot designates the type (class) of the instance, analogous to LinkML's designates_type._



<div data-search-exclude markdown="1">



URI: [linkmlmap:type_designator](https://w3id.org/linkml/transformer/type_designator)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Boolean](Boolean.md) |
| Domain Of | [SlotDerivation](SlotDerivation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [SlotDerivation](SlotDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:type_designator |
| native | linkmlmap:type_designator |




## LinkML Source

<details>
```yaml
name: type_designator
description: True if this target slot designates the type (class) of the instance,
  analogous to LinkML's designates_type.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: boolean

```
</details></div>