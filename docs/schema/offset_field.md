---
search:
  boost: 5.0
---

# Slot: offset_field 


_Name of the field in the source object that contains the offset amount. This value will be multiplied by offset_value._



<div data-search-exclude markdown="1">



URI: [linkmlmap:offset_field](https://w3id.org/linkml/transformer/offset_field)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Offset](Offset.md) | Configuration for calculating a value by applying an offset to a baseline val... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [Offset](Offset.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [Offset](Offset.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:offset_field |
| native | linkmlmap:offset_field |




## LinkML Source

<details>
```yaml
name: offset_field
description: Name of the field in the source object that contains the offset amount.
  This value will be multiplied by offset_value.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: Offset
domain_of:
- Offset
range: string
required: true

```
</details></div>