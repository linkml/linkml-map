---
search:
  boost: 5.0
---

# Slot: slot_name_template 


_Template for generating target slot names. Supports {variable} and {unit}._



<div data-search-exclude markdown="1">



URI: [linkmlmap:slot_name_template](https://w3id.org/linkml/transformer/slot_name_template)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [PivotOperation](PivotOperation.md) | An operation that reshapes data between wide and long (EAV) representations, ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [PivotOperation](PivotOperation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `string({variable})` |
| Owner | [PivotOperation](PivotOperation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:slot_name_template |
| native | linkmlmap:slot_name_template |




## LinkML Source

<details>
```yaml
name: slot_name_template
description: Template for generating target slot names. Supports {variable} and {unit}.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
ifabsent: string({variable})
owner: PivotOperation
domain_of:
- PivotOperation
range: string

```
</details></div>