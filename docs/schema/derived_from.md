---
search:
  boost: 0.5
---

# Slot: derived_from  <span style="color: red;"><strong> (DEPRECATED) </strong></span> 


_Deprecated. This field is ignored by the runtime and will be removed. It was intended to list source slots feeding into an expr-based derivation, but this information is fully derivable from the expr itself._



<div data-search-exclude markdown="1">



URI: [linkmlmap:derived_from](https://w3id.org/linkml/transformer/derived_from)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [SlotReference](SlotReference.md) |
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
| self | linkmlmap:derived_from |
| native | linkmlmap:derived_from |




## LinkML Source

<details>
```yaml
name: derived_from
description: Deprecated. This field is ignored by the runtime and will be removed.
  It was intended to list source slots feeding into an expr-based derivation, but
  this information is fully derivable from the expr itself.
deprecated: This field is fully derivable from expr and is not used by the runtime.
  It will be removed in a future version.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: SlotReference
multivalued: true

```
</details></div>