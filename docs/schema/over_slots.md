---
search:
  boost: 5.0
---

# Slot: over_slots 


_The source slots whose values are combined into the stringified result._



<div data-search-exclude markdown="1">



URI: [linkmlmap:over_slots](https://w3id.org/linkml/transformer/over_slots)
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
| Multivalued | Yes |
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
| self | linkmlmap:over_slots |
| native | linkmlmap:over_slots |




## LinkML Source

<details>
```yaml
name: over_slots
description: The source slots whose values are combined into the stringified result.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: StringificationConfiguration
domain_of:
- StringificationConfiguration
range: string
multivalued: true

```
</details></div>