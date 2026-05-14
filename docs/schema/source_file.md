---
search:
  boost: 5.0
---

# Slot: source_file 


_Optional file path or URL from which the schema can be loaded._



<div data-search-exclude markdown="1">



URI: [linkmlmap:source_file](https://w3id.org/linkml/transformer/source_file)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SchemaReference](SchemaReference.md) | A reference to a LinkML schema, with optional version and locator metadata |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [SchemaReference](SchemaReference.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [SchemaReference](SchemaReference.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:source_file |
| native | linkmlmap:source_file |




## LinkML Source

<details>
```yaml
name: source_file
description: Optional file path or URL from which the schema can be loaded.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SchemaReference
domain_of:
- SchemaReference
range: string

```
</details></div>