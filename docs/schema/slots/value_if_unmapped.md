---
search:
  boost: 5.0
---

# Slot: value_if_unmapped 


_The value to emit when a present source value matches no key in value_mappings or expression_mappings. Without it, such a value comes out null._



<div data-search-exclude markdown="1">



URI: [linkmlmap:slot/value_if_unmapped](https://w3id.org/linkml/transformer/slot/value_if_unmapped)
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
| self | linkmlmap:value_if_unmapped |
| native | linkmlmap:value_if_unmapped |




## LinkML Source

<details>
```yaml
name: value_if_unmapped
description: The value to emit when a present source value matches no key in value_mappings
  or expression_mappings. Without it, such a value comes out null.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: Any

```
</details></div>