

# Slot: expression_to_value_mappings


_A mapping table in which the keys are expressions_



URI: [linkmltr:expression_to_value_mappings](https://w3id.org/linkml/transformer/expression_to_value_mappings)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [EnumDerivation](EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enu... |  no  |
| [ClassDerivation](ClassDerivation.md) | A specification of how to derive a target class from a source class |  no  |
| [PrefixDerivation](PrefixDerivation.md) |  |  no  |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | A specification of how to derive the value of a PV from a source enum |  no  |
| [ElementDerivation](ElementDerivation.md) | An abstract grouping for classes that provide a specification of how to  deri... |  no  |







## Properties

* Range: [KeyVal](KeyVal.md)

* Multivalued: True





## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer




## LinkML Source

<details>
```yaml
name: expression_to_value_mappings
description: A mapping table in which the keys are expressions
from_schema: https://w3id.org/linkml/transformer
rank: 1000
multivalued: true
alias: expression_to_value_mappings
owner: ElementDerivation
domain_of:
- ElementDerivation
range: KeyVal
inlined: true

```
</details>