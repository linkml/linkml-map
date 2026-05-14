---
search:
  boost: 5.0
---

# Slot: description 


_description of the specification component_



<div data-search-exclude markdown="1">



URI: [dcterms:description](http://purl.org/dc/terms/description)
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
| Range | NONE |
| Domain Of | [SpecificationComponent](SpecificationComponent.md) |
| Slot URI | [dcterms:description](http://purl.org/dc/terms/description) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
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
| self | dcterms:description |
| native | linkmlmap:description |




## LinkML Source

<details>
```yaml
name: description
description: description of the specification component
from_schema: https://w3id.org/linkml/transformer
rank: 1000
slot_uri: dcterms:description
owner: SpecificationComponent
domain_of:
- SpecificationComponent

```
</details></div>