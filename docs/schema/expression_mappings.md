---
search:
  boost: 5.0
---

# Slot: expression_mappings 


_A mapping table where the values are expressions evaluated against source bindings. Looked up by the same key as value_mappings (the stringified source value). Keys should always be quoted (see value_mappings). If both value_mappings and expression_mappings are present, value_mappings takes precedence for keys that appear in both._



<div data-search-exclude markdown="1">



URI: [linkmlmap:expression_mappings](https://w3id.org/linkml/transformer/expression_mappings)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ElementDerivation](ElementDerivation.md) | An abstract grouping for classes that provide a specification of how to deriv... |  no  |
| [ClassDerivation](ClassDerivation.md) | A specification of how to derive a target class from a source class |  no  |
| [ObjectDerivation](ObjectDerivation.md) | Deprecated |  no  |
| [SlotDerivation](SlotDerivation.md) | A specification of how to derive the value of a target slot from a source slo... |  no  |
| [EnumDerivation](EnumDerivation.md) | A specification of how to derive the value of a target enum from a source enu... |  no  |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | A specification of how to derive the value of a PV from a source enum |  no  |
| [PrefixDerivation](PrefixDerivation.md) | A specification of how to derive a target prefix declaration |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [KeyVal](KeyVal.md) |
| Domain Of | [ElementDerivation](ElementDerivation.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ElementDerivation](ElementDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:expression_mappings |
| native | linkmlmap:expression_mappings |




## LinkML Source

<details>
```yaml
name: expression_mappings
description: A mapping table where the values are expressions evaluated against source
  bindings. Looked up by the same key as value_mappings (the stringified source value).
  Keys should always be quoted (see value_mappings). If both value_mappings and expression_mappings
  are present, value_mappings takes precedence for keys that appear in both.
from_schema: https://w3id.org/linkml/transformer
rank: 1000
owner: ElementDerivation
domain_of:
- ElementDerivation
range: KeyVal
multivalued: true
inlined: true

```
</details></div>