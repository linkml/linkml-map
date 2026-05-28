---
search:
  boost: 5.0
---

# Slot: source_schema_patches 


_Schema patches to apply to the source schema before transformation. Useful for adding foreign key relationships to auto-generated schemas. Uses LinkML schema YAML structure (classes, slots, attributes, etc.)._



<div data-search-exclude markdown="1">



URI: [linkmlmap:source_schema_patches](https://w3id.org/linkml/transformer/source_schema_patches)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | A collection of mappings between source and target classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Any](Any.md) |
| Domain Of | [TransformationSpecification](TransformationSpecification.md) |

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
| self | linkmlmap:source_schema_patches |
| native | linkmlmap:source_schema_patches |




## LinkML Source

<details>
```yaml
name: source_schema_patches
description: Schema patches to apply to the source schema before transformation. Useful
  for adding foreign key relationships to auto-generated schemas. Uses LinkML schema
  YAML structure (classes, slots, attributes, etc.).
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: TransformationSpecification
domain_of:
- TransformationSpecification
range: Any

```
</details></div>