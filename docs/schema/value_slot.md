---
search:
  boost: 5.0
---

# Slot: value_slot 


_Slot to use for the value column in the melted/long representation. In EAV this is the name of the 'V' variable_



<div data-search-exclude markdown="1">



URI: [linkmlmap:value_slot](https://w3id.org/linkml/transformer/value_slot)
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
### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `string(value)` |
| Owner | [PivotOperation](PivotOperation.md) |









## Aliases


* value_name




## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:value_slot |
| native | linkmlmap:value_slot |




## LinkML Source

<details>
```yaml
name: value_slot
description: Slot to use for the value column in the melted/long representation. In
  EAV this is the name of the 'V' variable
from_schema: https://w3id.org/linkml/transformer
aliases:
- value_name
rank: 1000
ifabsent: string(value)
owner: PivotOperation
domain_of:
- PivotOperation
range: SlotReference

```
</details></div>