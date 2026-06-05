---
search:
  boost: 5.0
---

# Slot: reversed 


_If true, reverse the operation, splitting a delimited or serialized string back into multiple values._



<div data-search-exclude markdown="1">



URI: [linkmlmap:reversed](https://w3id.org/linkml/transformer/reversed)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [StringificationConfiguration](StringificationConfiguration.md) | Configuration for collapsing multiple values into a single delimited or seria... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Boolean](Boolean.md) |
| Domain Of | [StringificationConfiguration](StringificationConfiguration.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [StringificationConfiguration](StringificationConfiguration.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:reversed |
| native | linkmlmap:reversed |




## LinkML Source

<details>
```yaml
name: reversed
description: If true, reverse the operation, splitting a delimited or serialized string
  back into multiple values.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: StringificationConfiguration
domain_of:
- StringificationConfiguration
range: boolean

```
</details></div>