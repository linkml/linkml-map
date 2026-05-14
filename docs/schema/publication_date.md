---
search:
  boost: 5.0
---

# Slot: publication_date 


_date of publication of this transformation specification_



<div data-search-exclude markdown="1">



URI: [dcterms:issued](http://purl.org/dc/terms/issued)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Date](Date.md) |
| Domain Of | [TransformationSpecification](TransformationSpecification.md) |
| Slot URI | [dcterms:issued](http://purl.org/dc/terms/issued) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [TransformationSpecification](TransformationSpecification.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | dcterms:issued |
| native | linkmlmap:publication_date |




## LinkML Source

<details>
```yaml
name: publication_date
description: date of publication of this transformation specification
from_schema: https://w3id.org/linkml/transformer
rank: 1000
slot_uri: dcterms:issued
owner: TransformationSpecification
domain_of:
- TransformationSpecification
range: date

```
</details></div>