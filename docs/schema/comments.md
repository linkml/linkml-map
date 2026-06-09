---
search:
  boost: 5.0
---

# Slot: comments 


_A list of comments about this component. Comments are free text, and may be used to provide additional information about the component, including instructions for its use._



<div data-search-exclude markdown="1">



URI: [rdfs:comment](http://www.w3.org/2000/01/rdf-schema#comment)
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
| [PrefixDerivation](PrefixDerivation.md) | A specification of how to derive a target prefix declaration |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [SpecificationComponent](SpecificationComponent.md) |
| Slot URI | [rdfs:comment](http://www.w3.org/2000/01/rdf-schema#comment) |

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
| self | rdfs:comment |
| native | linkmlmap:comments |




## LinkML Source

<details>
```yaml
name: comments
description: A list of comments about this component. Comments are free text, and
  may be used to provide additional information about the component, including instructions
  for its use.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
slot_uri: rdfs:comment
owner: SpecificationComponent
domain_of:
- SpecificationComponent
range: string
multivalued: true

```
</details></div>