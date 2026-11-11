---
search:
  boost: 5.0
---

# Slot: value_if_missing 


_The value to emit when the populated_from source value is missing: an empty cell, an absent column, or a code nulled by missing_values. It is a target value, so value_mappings and offset don't apply to it._



<div data-search-exclude markdown="1">



URI: [linkmlmap:slot/value_if_missing](https://w3id.org/linkml/transformer/slot/value_if_missing)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](../classes/SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Any](../classes/Any.md) |
| Domain Of | [SlotDerivation](../classes/SlotDerivation.md) |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [SlotDerivation](../classes/SlotDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:value_if_missing |
| native | linkmlmap:value_if_missing |




## LinkML Source

<details>
```yaml
name: value_if_missing
description: 'The value to emit when the populated_from source value is missing: an
  empty cell, an absent column, or a code nulled by missing_values. It is a target
  value, so value_mappings and offset don''t apply to it.'
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: Any

```
</details></div>