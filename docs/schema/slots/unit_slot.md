---
search:
  boost: 5.0
---

# Slot: unit_slot 


_Optional slot containing unit information for {variable}_{unit} naming_



<div data-search-exclude markdown="1">



URI: [linkmlmap:slot/unit_slot](https://w3id.org/linkml/transformer/slot/unit_slot)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [PivotOperation](../classes/PivotOperation.md) | An operation that reshapes data between wide and long (EAV) representations, ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [SlotReference](../types/SlotReference.md) |
| Domain Of | [PivotOperation](../classes/PivotOperation.md) |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [PivotOperation](../classes/PivotOperation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:unit_slot |
| native | linkmlmap:unit_slot |




## LinkML Source

<details>
```yaml
name: unit_slot
description: Optional slot containing unit information for {variable}_{unit} naming
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: PivotOperation
domain_of:
- PivotOperation
range: SlotReference

```
</details></div>