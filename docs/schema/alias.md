---
search:
  boost: 5.0
---

# Slot: alias 


_name of the class to be aliased_



<div data-search-exclude markdown="1">



URI: [linkmlmap:alias](https://w3id.org/linkml/transformer/alias)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [AliasedClass](AliasedClass.md) | alias-class key value pairs for classes |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | NONE |
| Domain Of | [AliasedClass](AliasedClass.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Key | Yes |
| Owner | [AliasedClass](AliasedClass.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:alias |
| native | linkmlmap:alias |




## LinkML Source

<details>
```yaml
name: alias
description: name of the class to be aliased
from_schema: https://w3id.org/linkml/transformer
rank: 1000
key: true
owner: AliasedClass
domain_of:
- AliasedClass
required: true

```
</details></div>