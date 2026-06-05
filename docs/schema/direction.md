---
search:
  boost: 5.0
---

# Slot: direction 


_Whether to MELT (wide to long) or UNMELT (long to wide)._



<div data-search-exclude markdown="1">



URI: [linkmlmap:direction](https://w3id.org/linkml/transformer/direction)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [PivotOperation](PivotOperation.md) | An operation that reshapes data between wide and long (EAV) representations, ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [PivotDirectionType](PivotDirectionType.md) |
| Domain Of | [PivotOperation](PivotOperation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
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
| self | linkmlmap:direction |
| native | linkmlmap:direction |




## LinkML Source

<details>
```yaml
name: direction
description: Whether to MELT (wide to long) or UNMELT (long to wide).
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: PivotOperation
domain_of:
- PivotOperation
range: PivotDirectionType
required: true

```
</details></div>