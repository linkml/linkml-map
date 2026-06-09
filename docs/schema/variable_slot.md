---
search:
  boost: 5.0
---

# Slot: variable_slot 


_Slot to use for the variable column in the melted/long representation. In EAV this is the name of the 'A' variable_



<div data-search-exclude markdown="1">



URI: [linkmlmap:variable_slot](https://w3id.org/linkml/transformer/variable_slot)
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
| If Absent | `string(variable)` |
| Owner | [PivotOperation](PivotOperation.md) |









## Aliases


* var_name




## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:variable_slot |
| native | linkmlmap:variable_slot |




## LinkML Source

<details>
```yaml
name: variable_slot
description: Slot to use for the variable column in the melted/long representation.
  In EAV this is the name of the 'A' variable
from_schema: https://w3id.org/linkml/transformer
aliases:
- var_name
rank: 1000
ifabsent: string(variable)
owner: PivotOperation
domain_of:
- PivotOperation
range: SlotReference

```
</details></div>