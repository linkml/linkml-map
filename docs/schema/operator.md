---
search:
  boost: 5.0
---

# Slot: operator 


_The aggregation function to apply (for example SUM, AVERAGE, COUNT)._



<div data-search-exclude markdown="1">



URI: [linkmlmap:operator](https://w3id.org/linkml/transformer/operator)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [AggregationOperation](AggregationOperation.md) | An operation that reduces multiple input values to a single value using an ag... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [AggregationType](AggregationType.md) |
| Domain Of | [AggregationOperation](AggregationOperation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [AggregationOperation](AggregationOperation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:operator |
| native | linkmlmap:operator |




## LinkML Source

<details>
```yaml
name: operator
description: The aggregation function to apply (for example SUM, AVERAGE, COUNT).
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: AggregationOperation
domain_of:
- AggregationOperation
range: AggregationType
required: true

```
</details></div>