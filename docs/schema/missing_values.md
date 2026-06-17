---
search:
  boost: 5.0
---

# Slot: missing_values 


_Source values to treat as missing and emit as null instead of the literal value — e.g. sentinel codes like -9, 99, or 999 meaning "not collected". Accepts a single value or a list._



<div data-search-exclude markdown="1">



URI: [linkmlmap:missing_values](https://w3id.org/linkml/transformer/missing_values)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Any](Any.md) |
| Domain Of | [SlotDerivation](SlotDerivation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
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
| self | linkmlmap:missing_values |
| native | linkmlmap:missing_values |




## LinkML Source

<details>
```yaml
name: missing_values
description: Source values to treat as missing and emit as null instead of the literal
  value — e.g. sentinel codes like -9, 99, or 999 meaning "not collected". Accepts
  a single value or a list.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: Any
multivalued: true

```
</details></div>