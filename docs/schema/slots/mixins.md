---
search:
  boost: 5.0
---

# Slot: mixins 


_Mixin elements applied to the derived target element._



<div data-search-exclude markdown="1">



URI: [linkml:mixins](https://w3id.org/linkml/mixins)
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
| Slot URI | [linkml:mixins](https://w3id.org/linkml/mixins) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |


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
| self | linkml:mixins |
| native | linkmlmap:mixins |




## LinkML Source

<details>
```yaml
name: mixins
description: Mixin elements applied to the derived target element.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
slot_uri: linkml:mixins
owner: ElementDerivation
domain_of:
- ElementDerivation
range: ElementDerivation
multivalued: true
inlined: false

```
</details></div>