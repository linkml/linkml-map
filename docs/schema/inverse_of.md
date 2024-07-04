

# Slot: inverse_of


_Used to specify a class-slot tuple that is the inverse of the derived/target slot. This is used primarily for mapping to relational databases or formalisms that do not allow multiple values. The class representing the repeated element has a foreign key slot inserted in that 'back references' the original multivalued slot._



URI: [linkmltr:inverse_of](https://w3id.org/linkml/transformer/inverse_of)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |







## Properties

* Range: [Inverse](Inverse.md)





## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer




## LinkML Source

<details>
```yaml
name: inverse_of
description: Used to specify a class-slot tuple that is the inverse of the derived/target
  slot. This is used primarily for mapping to relational databases or formalisms that
  do not allow multiple values. The class representing the repeated element has a
  foreign key slot inserted in that 'back references' the original multivalued slot.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
alias: inverse_of
owner: SlotDerivation
domain_of:
- SlotDerivation
range: Inverse

```
</details>