---
search:
  boost: 0.5
---

# Slot: object_derivations  <span style="color: red;"><strong> (DEPRECATED) </strong></span> 


_Deprecated. Use list-based class_derivations instead. One or more object derivations used to construct the slot value(s), which must be instances of a class._



<div data-search-exclude markdown="1">



URI: [linkmlmap:object_derivations](https://w3id.org/linkml/transformer/object_derivations)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ObjectDerivation](ObjectDerivation.md) |
| Domain Of | [SlotDerivation](SlotDerivation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
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
| self | linkmlmap:object_derivations |
| native | linkmlmap:object_derivations |




## LinkML Source

<details>
```yaml
name: object_derivations
description: Deprecated. Use list-based class_derivations instead. One or more object
  derivations used to construct the slot value(s), which must be instances of a class.
deprecated: Use list-based class_derivations instead of nesting via object_derivations.
  See https://github.com/linkml/linkml-map/issues/112
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: ObjectDerivation
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>