

# Slot: derived_from


_Source slots that are used to derive this slot. This can be computed from the expr, if the expr is declarative._



URI: [linkmltr:derived_from](https://w3id.org/linkml/transformer/derived_from)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |







## Properties

* Range: [SlotReference](SlotReference.md)

* Multivalued: True





## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer




## LinkML Source

<details>
```yaml
name: derived_from
description: Source slots that are used to derive this slot. This can be computed
  from the expr, if the expr is declarative.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
multivalued: true
alias: derived_from
owner: SlotDerivation
domain_of:
- SlotDerivation
range: SlotReference

```
</details>