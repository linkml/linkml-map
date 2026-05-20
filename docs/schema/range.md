---
search:
  boost: 5.0
---

# Slot: range 

<div data-search-exclude markdown="1">



URI: [linkml:range](https://w3id.org/linkml/range)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [SlotDerivation](SlotDerivation.md) |
| Slot URI | [linkml:range](https://w3id.org/linkml/range) |

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
| self | linkml:range |
| native | linkmlmap:range |




## LinkML Source

<details>
```yaml
name: range
from_schema: https://w3id.org/linkml/transformer
rank: 1000
slot_uri: linkml:range
owner: SlotDerivation
domain_of:
- SlotDerivation
range: string

```
</details></div>