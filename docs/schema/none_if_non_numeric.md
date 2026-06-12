---
search:
  boost: 5.0
---

# Slot: none_if_non_numeric 


_If true, return None when the source value cannot be coerced to a numeric type instead of raising an error. This is an explicit opt-in for columns that contain non-numeric coded values (e.g. 'A', 'M') mixed with numeric data._



<div data-search-exclude markdown="1">



URI: [linkmlmap:none_if_non_numeric](https://w3id.org/linkml/transformer/none_if_non_numeric)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [UnitConversionConfiguration](UnitConversionConfiguration.md) | Configuration for converting a slot value from a source unit of measure to a ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Boolean](Boolean.md) |
| Domain Of | [UnitConversionConfiguration](UnitConversionConfiguration.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [UnitConversionConfiguration](UnitConversionConfiguration.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:none_if_non_numeric |
| native | linkmlmap:none_if_non_numeric |




## LinkML Source

<details>
```yaml
name: none_if_non_numeric
description: If true, return None when the source value cannot be coerced to a numeric
  type instead of raising an error. This is an explicit opt-in for columns that contain
  non-numeric coded values (e.g. 'A', 'M') mixed with numeric data.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: UnitConversionConfiguration
domain_of:
- UnitConversionConfiguration
range: boolean

```
</details></div>