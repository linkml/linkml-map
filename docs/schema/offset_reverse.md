---
search:
  boost: 5.0
---

# Slot: offset_reverse 


_If true, subtract the offset from the baseline (baseline - offset). If false, add the offset to the baseline (baseline + offset). Defaults to false (addition)._



<div data-search-exclude markdown="1">



URI: [linkmlmap:offset_reverse](https://w3id.org/linkml/transformer/offset_reverse)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Offset](Offset.md) | Configuration for calculating a value by applying an offset to a baseline val... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Boolean](Boolean.md) |
| Domain Of | [Offset](Offset.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
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
| self | linkmlmap:offset_reverse |
| native | linkmlmap:offset_reverse |




## LinkML Source

<details>
```yaml
name: offset_reverse
description: If true, subtract the offset from the baseline (baseline - offset). If
  false, add the offset to the baseline (baseline + offset). Defaults to false (addition).
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: Offset
domain_of:
- Offset
range: boolean

```
</details></div>