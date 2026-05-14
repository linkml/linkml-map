---
search:
  boost: 5.0
---

# Slot: schema_uri 


_The URI/IRI identifier of the schema (matches the schema's `id`)._



<div data-search-exclude markdown="1">



URI: [linkmlmap:schema_uri](https://w3id.org/linkml/transformer/schema_uri)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SchemaReference](SchemaReference.md) | A reference to a LinkML schema, with optional version and locator metadata |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Uri](Uri.md) |
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
| self | linkmlmap:schema_uri |
| native | linkmlmap:schema_uri |




## LinkML Source

<details>
```yaml
name: schema_uri
description: The URI/IRI identifier of the schema (matches the schema's `id`).
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: SchemaReference
domain_of:
- SchemaReference
range: uri

```
</details></div>