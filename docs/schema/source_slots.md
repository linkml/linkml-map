---
search:
  boost: 5.0
---

# Slot: source_slots 


_For MELT, the list of wide-format slots to melt_



<div data-search-exclude markdown="1">



URI: [linkmlmap:source_slots](https://w3id.org/linkml/transformer/source_slots)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [PivotOperation](PivotOperation.md) |  |  no  |






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
| self | linkmlmap:source_slots |
| native | linkmlmap:source_slots |




## LinkML Source

<details>
```yaml
name: source_slots
description: For MELT, the list of wide-format slots to melt
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: PivotOperation
domain_of:
- PivotOperation
range: SlotReference
multivalued: true

```
</details></div>