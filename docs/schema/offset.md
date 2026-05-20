---
search:
  boost: 5.0
---

# Slot: offset 


_Configuration for calculating a value by applying an offset to a baseline value. The baseline value comes from the slot's populated_from field. This is commonly used for longitudinal data where measurements are recorded relative to a baseline. For example, calculating age_at_visit from age + (days * 1/365)._



<div data-search-exclude markdown="1">



URI: [linkmlmap:offset](https://w3id.org/linkml/transformer/offset)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Offset](Offset.md) |
| Domain Of | [SlotDerivation](SlotDerivation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [SlotDerivation](SlotDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:offset |
| native | linkmlmap:offset |




## LinkML Source

<details>
```yaml
name: offset
description: Configuration for calculating a value by applying an offset to a baseline
  value. The baseline value comes from the slot's populated_from field. This is commonly
  used for longitudinal data where measurements are recorded relative to a baseline.
  For example, calculating age_at_visit from age + (days * 1/365).
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: Offset

```
</details></div>