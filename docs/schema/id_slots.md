---
search:
  boost: 5.0
---

# Slot: id_slots 


_Slots that identify the entity (not pivoted)_



<div data-search-exclude markdown="1">



URI: [linkmlmap:id_slots](https://w3id.org/linkml/transformer/id_slots)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [PivotOperation](PivotOperation.md) | An operation that reshapes data between wide and long (EAV) representations, ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [SlotReference](SlotReference.md) |
| Domain Of | [PivotOperation](PivotOperation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [PivotOperation](PivotOperation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:id_slots |
| native | linkmlmap:id_slots |




## LinkML Source

<details>
```yaml
name: id_slots
description: Slots that identify the entity (not pivoted)
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: PivotOperation
domain_of:
- PivotOperation
range: SlotReference
multivalued: true

```
</details></div>