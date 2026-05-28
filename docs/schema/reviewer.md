---
search:
  boost: 5.0
---

# Slot: reviewer 


_A list of reviewers of this transformation specification_



<div data-search-exclude markdown="1">



URI: [linkmlmap:reviewer](https://w3id.org/linkml/transformer/reviewer)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Agent](Agent.md) |
| Domain Of | [TransformationSpecification](TransformationSpecification.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
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
| self | linkmlmap:reviewer |
| native | linkmlmap:reviewer |




## LinkML Source

<details>
```yaml
name: reviewer
description: A list of reviewers of this transformation specification
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: TransformationSpecification
domain_of:
- TransformationSpecification
range: Agent
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>