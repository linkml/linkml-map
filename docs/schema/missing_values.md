---
search:
  boost: 5.0
---

# Slot: missing_values 


_Source values that represent a missing observation and should be emitted as null instead of the literal value. Useful for sentinel/missing-value codes common in survey and clinical data (e.g. an age of -9, or codes like 99, 999, -1000 meaning "not collected"). Matching is by string equality against the source value, so listing -9 nulls -9 but not 99. Applied to a value pulled from a source column (via populated_from or a bare same-named slot), before any mappings, offset, or range coercion. It is not applied to a constant value:, a computed expr:, the deprecated sources:, or the object-valued slot that declares nested class_derivations — but it does apply to scalar slot derivations within a nested class_derivation._



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
description: Source values that represent a missing observation and should be emitted
  as null instead of the literal value. Useful for sentinel/missing-value codes common
  in survey and clinical data (e.g. an age of -9, or codes like 99, 999, -1000 meaning
  "not collected"). Matching is by string equality against the source value, so listing
  -9 nulls -9 but not 99. Applied to a value pulled from a source column (via populated_from
  or a bare same-named slot), before any mappings, offset, or range coercion. It is
  not applied to a constant value:, a computed expr:, the deprecated sources:, or
  the object-valued slot that declares nested class_derivations — but it does apply
  to scalar slot derivations within a nested class_derivation.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SlotDerivation
domain_of:
- SlotDerivation
range: Any
multivalued: true

```
</details></div>