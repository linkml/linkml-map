---
search:
  boost: 5.0
---

# Slot: delimiter 


_Delimiter used to join multiple values into a single string._



<div data-search-exclude markdown="1">



URI: [linkmlmap:delimiter](https://w3id.org/linkml/transformer/delimiter)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [StringificationConfiguration](StringificationConfiguration.md) | Configuration for collapsing multiple values into a single delimited or seria... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [StringificationConfiguration](StringificationConfiguration.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [StringificationConfiguration](StringificationConfiguration.md) |











## Examples

| Value |
| --- |
| , |
| | |
| ; |



## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:delimiter |
| native | linkmlmap:delimiter |




## LinkML Source

<details>
```yaml
name: delimiter
description: Delimiter used to join multiple values into a single string.
examples:
- value: ','
- value: '|'
- value: ;
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: StringificationConfiguration
domain_of:
- StringificationConfiguration
range: string

```
</details></div>