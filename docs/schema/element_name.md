---
search:
  boost: 5.0
---

# Slot: element_name 


_Name of the source element (class, slot, enum, etc.) this directive applies to._



<div data-search-exclude markdown="1">



URI: [linkmlmap:element_name](https://w3id.org/linkml/transformer/element_name)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [CopyDirective](CopyDirective.md) | Instructs a Schema Mapper in how to map to a target schema |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | NONE |
| Domain Of | [CopyDirective](CopyDirective.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Key | Yes |
| Owner | [CopyDirective](CopyDirective.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:element_name |
| native | linkmlmap:element_name |




## LinkML Source

<details>
```yaml
name: element_name
description: Name of the source element (class, slot, enum, etc.) this directive applies
  to.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
key: true
owner: CopyDirective
domain_of:
- CopyDirective
required: true

```
</details></div>