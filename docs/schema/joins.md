

# Slot: joins


_Additional classes to be joined to derive instances of the target class_



URI: [linkmltr:joins](https://w3id.org/linkml/transformer/joins)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ClassDerivation](ClassDerivation.md) | A specification of how to derive a target class from a source class |  no  |







## Properties

* Range: [AliasedClass](AliasedClass.md)

* Multivalued: True





## Comments

* supports cross-table lookups via source_key/lookup_key or the join_on field

## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer




## LinkML Source

<details>
```yaml
name: joins
description: Additional classes to be joined to derive instances of the target class
comments:
- supports cross-table lookups via source_key/lookup_key or the join_on field
from_schema: https://w3id.org/linkml/transformer
rank: 1000
multivalued: true
alias: joins
owner: ClassDerivation
domain_of:
- ClassDerivation
range: AliasedClass
inlined: true

```
</details>
