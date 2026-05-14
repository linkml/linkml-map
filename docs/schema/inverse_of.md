---
search:
  boost: 5.0
---

# Slot: inverse_of 


_Used to specify a class-slot tuple that is the inverse of the derived/target slot. This is used primarily for mapping to relational databases or formalisms that do not allow multiple values. The class representing the repeated element has a foreign key slot inserted in that 'back references' the original multivalued slot._



<div data-search-exclude markdown="1">



URI: [linkmlmap:inverse_of](https://w3id.org/linkml/transformer/inverse_of)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Inverse](Inverse.md) |
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
| self | linkmlmap:inverse_of |
| native | linkmlmap:inverse_of |




## LinkML Source

<details>
```yaml
name: inverse_of
description: Used to specify a class-slot tuple that is the inverse of the derived/target
  slot. This is used primarily for mapping to relational databases or formalisms that
  do not allow multiple values. The class representing the repeated element has a
  foreign key slot inserted in that 'back references' the original multivalued slot.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: Inverse

```
</details></div>