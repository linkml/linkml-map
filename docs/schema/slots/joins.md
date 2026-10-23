---
search:
  boost: 5.0
---

# Slot: joins 


_Additional classes to be joined to derive instances of the target class_



<div data-search-exclude markdown="1">



URI: [linkmlmap:slot/joins](https://w3id.org/linkml/transformer/slot/joins)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ClassDerivation](../classes/ClassDerivation.md) | A specification of how to derive a target class from a source class |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [AliasedClass](../classes/AliasedClass.md) |
| Domain Of | [ClassDerivation](../classes/ClassDerivation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ClassDerivation](../classes/ClassDerivation.md) |










## Comments

* supports cross-table lookups via source_key/lookup_key or the join_on field



## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:joins |
| native | linkmlmap:joins |




## LinkML Source

<details>
```yaml
name: joins
description: Additional classes to be joined to derive instances of the target class
comments:
- supports cross-table lookups via source_key/lookup_key or the join_on field
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: ClassDerivation
domain_of:
- ClassDerivation
range: AliasedClass
multivalued: true
inlined: true

```
</details></div>