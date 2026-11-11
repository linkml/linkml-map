---
search:
  boost: 5.0
---

# Slot: filter_rows 


_An expression evaluated on each source row, using the LinkML expression language. A row for which it is not true yields no object: no record at the top level, and no nested object under a slot._



<div data-search-exclude markdown="1">



URI: [linkmlmap:slot/filter_rows](https://w3id.org/linkml/transformer/slot/filter_rows)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ClassDerivation](../classes/ClassDerivation.md) | A specification of how to derive a target class from a source class |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](../types/String.md) |
| Domain Of | [ClassDerivation](../classes/ClassDerivation.md) |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ClassDerivation](../classes/ClassDerivation.md) |











## Examples

| Value |
| --- |
| {visit_code} == 3 |



## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:filter_rows |
| native | linkmlmap:filter_rows |




## LinkML Source

<details>
```yaml
name: filter_rows
description: 'An expression evaluated on each source row, using the LinkML expression
  language. A row for which it is not true yields no object: no record at the top
  level, and no nested object under a slot.'
examples:
- value: '{visit_code} == 3'
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: ClassDerivation
domain_of:
- ClassDerivation
range: string

```
</details></div>