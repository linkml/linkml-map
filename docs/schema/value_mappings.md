---
search:
  boost: 5.0
---

# Slot: value_mappings 


_A mapping table that is applied directly to mappings, in order of precedence. Keys should always be quoted in YAML to prevent type coercion — unquoted true/false become booleans and bare numbers become integers, which will not match the stringified source value used for lookup._



<div data-search-exclude markdown="1">



URI: [linkmlmap:value_mappings](https://w3id.org/linkml/transformer/value_mappings)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ElementDerivation](ElementDerivation.md) | An abstract grouping for classes that provide a specification of how to deriv... |  no  |
| [ClassDerivation](ClassDerivation.md) | A specification of how to derive a target class from a source class |  no  |
| [ObjectDerivation](ObjectDerivation.md) | Deprecated |  no  |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |
| [EnumDerivation](EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enu... |  no  |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | A specification of how to derive the value of a PV from a source enum |  no  |
| [PrefixDerivation](PrefixDerivation.md) |  |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [KeyVal](KeyVal.md) |
| Domain Of | [ElementDerivation](ElementDerivation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ElementDerivation](ElementDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:value_mappings |
| native | linkmlmap:value_mappings |




## LinkML Source

<details>
```yaml
name: value_mappings
description: A mapping table that is applied directly to mappings, in order of precedence.
  Keys should always be quoted in YAML to prevent type coercion — unquoted true/false
  become booleans and bare numbers become integers, which will not match the stringified
  source value used for lookup.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: ElementDerivation
domain_of:
- ElementDerivation
range: KeyVal
multivalued: true
inlined: true

```
</details></div>