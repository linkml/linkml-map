---
search:
  boost: 5.0
---

# Slot: implements 


_A reference to a specification that this component implements._



<div data-search-exclude markdown="1">



URI: [linkmlmap:implements](https://w3id.org/linkml/transformer/implements)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SpecificationComponent](SpecificationComponent.md) |  |  no  |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |
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
| Range | [Uriorcurie](Uriorcurie.md) |
| Domain Of | [SpecificationComponent](SpecificationComponent.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [SpecificationComponent](SpecificationComponent.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:implements |
| native | linkmlmap:implements |




## LinkML Source

<details>
```yaml
name: implements
description: A reference to a specification that this component implements.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SpecificationComponent
domain_of:
- SpecificationComponent
range: uriorcurie
multivalued: true

```
</details></div>