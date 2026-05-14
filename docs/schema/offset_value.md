---
search:
  boost: 5.0
---

# Slot: offset_value 


_Multiplier applied to the offset field value. For example, use 1/365 (or 0.00273973) to convert days to years, or 1/12 (or 0.0833333) to convert months to years._



<div data-search-exclude markdown="1">



URI: [linkmlmap:offset_value](https://w3id.org/linkml/transformer/offset_value)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Offset](Offset.md) | Configuration for calculating a value by applying an offset to a baseline val... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Float](Float.md) |
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
| self | linkmlmap:offset_value |
| native | linkmlmap:offset_value |




## LinkML Source

<details>
```yaml
name: offset_value
description: Multiplier applied to the offset field value. For example, use 1/365
  (or 0.00273973) to convert days to years, or 1/12 (or 0.0833333) to convert months
  to years.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: Offset
domain_of:
- Offset
range: float
required: true

```
</details></div>