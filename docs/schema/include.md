---
search:
  boost: 5.0
---

# Slot: include 


_Add certain sub-elements to the list of sub-elements to be copied._

_As of now there it is under-specified, how to specify the sub-elements to include. One possible implementation would be a list where all element types can be mixed, since there might not be name conflicts across element types._



<div data-search-exclude markdown="1">



URI: [linkmlmap:include](https://w3id.org/linkml/transformer/include)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [CopyDirective](CopyDirective.md) | Instructs a Schema Mapper in how to map to a target schema |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Any](Any.md) |
| Domain Of | [CopyDirective](CopyDirective.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [CopyDirective](CopyDirective.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:include |
| native | linkmlmap:include |




## LinkML Source

<details>
```yaml
name: include
description: 'Add certain sub-elements to the list of sub-elements to be copied.

  As of now there it is under-specified, how to specify the sub-elements to include.
  One possible implementation would be a list where all element types can be mixed,
  since there might not be name conflicts across element types.'
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: CopyDirective
domain_of:
- CopyDirective
range: Any

```
</details></div>