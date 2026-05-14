---
search:
  boost: 5.0
---

# Slot: mixins 

<div data-search-exclude markdown="1">



URI: [linkml:mixins](https://w3id.org/linkml/mixins)
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
| Range | [ElementDerivation](ElementDerivation.md) |
| Domain Of | [ElementDerivation](ElementDerivation.md) |
| Slot URI | [linkml:mixins](https://w3id.org/linkml/mixins) |

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
| self | linkml:mixins |
| native | linkmlmap:mixins |




## LinkML Source

<details>
```yaml
name: mixins
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