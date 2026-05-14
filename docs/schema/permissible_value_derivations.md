---
search:
  boost: 5.0
---

# Slot: permissible_value_derivations 


_Instructions on how to derive a set of PVs in the target schema_



<div data-search-exclude markdown="1">



URI: [linkmlmap:permissible_value_derivations](https://w3id.org/linkml/transformer/permissible_value_derivations)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [EnumDerivation](EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enu... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [PermissibleValueDerivation](PermissibleValueDerivation.md) |
| Domain Of | [EnumDerivation](EnumDerivation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [EnumDerivation](EnumDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:permissible_value_derivations |
| native | linkmlmap:permissible_value_derivations |




## LinkML Source

<details>
```yaml
name: permissible_value_derivations
description: Instructions on how to derive a set of PVs in the target schema
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: EnumDerivation
domain_of:
- EnumDerivation
range: PermissibleValueDerivation
multivalued: true
inlined: true

```
</details></div>