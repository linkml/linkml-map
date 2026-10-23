---
search:
  boost: 5.0
---

# Slot: is_a 


_The parent element that the derived target element inherits from._



<div data-search-exclude markdown="1">



URI: [linkml:is_a](https://w3id.org/linkml/is_a)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ElementDerivation](../classes/ElementDerivation.md) | An abstract grouping for classes that provide a specification of how to deriv... |  no  |
| [ClassDerivation](../classes/ClassDerivation.md) | A specification of how to derive a target class from a source class |  no  |
| [ObjectDerivation](../classes/ObjectDerivation.md) | Deprecated |  no  |
| [SlotDerivation](../classes/SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |
| [EnumDerivation](../classes/EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enu... |  no  |
| [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md) | A specification of how to derive the value of a PV from a source enum |  no  |
| [PrefixDerivation](../classes/PrefixDerivation.md) | A specification of how to derive a target prefix declaration |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ElementDerivation](../classes/ElementDerivation.md) |
| Domain Of | [ElementDerivation](../classes/ElementDerivation.md) |
| Slot URI | [linkml:is_a](https://w3id.org/linkml/is_a) |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ElementDerivation](../classes/ElementDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkml:is_a |
| native | linkmlmap:is_a |




## LinkML Source

<details>
```yaml
name: is_a
description: The parent element that the derived target element inherits from.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
slot_uri: linkml:is_a
owner: ElementDerivation
domain_of:
- ElementDerivation
range: ElementDerivation

```
</details></div>