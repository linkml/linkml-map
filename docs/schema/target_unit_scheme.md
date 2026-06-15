---
search:
  boost: 5.0
---

# Slot: target_unit_scheme 


_The unit scheme or system identifying target_unit (for example ucum)._



<div data-search-exclude markdown="1">



URI: [linkmlmap:target_unit_scheme](https://w3id.org/linkml/transformer/target_unit_scheme)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [UnitConversionConfiguration](UnitConversionConfiguration.md) | Configuration for converting a slot value from a source unit of measure to a ... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [UnitConversionConfiguration](UnitConversionConfiguration.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [UnitConversionConfiguration](UnitConversionConfiguration.md) |











## Examples

| Value |
| --- |
| ucum |



## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:target_unit_scheme |
| native | linkmlmap:target_unit_scheme |




## LinkML Source

<details>
```yaml
name: target_unit_scheme
description: The unit scheme or system identifying target_unit (for example ucum).
examples:
- value: ucum
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: UnitConversionConfiguration
domain_of:
- UnitConversionConfiguration
range: string

```
</details></div>