---
search:
  boost: 10.0
---

# Class: KeyVal 


_A generic key-value pair._



<div data-search-exclude markdown="1">



URI: [linkmlmap:class/KeyVal](https://w3id.org/linkml/transformer/class/KeyVal)





```mermaid
 classDiagram
    class KeyVal
    click KeyVal href "../../classes/KeyVal/"
      KeyVal : key
        
      KeyVal : value
        
          
    
        
        
        KeyVal --> "0..1" Any : value
        click Any href "../../classes/Any/"
    

        
      
```




<!-- no inheritance hierarchy -->

## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [key](../slots/key.md) | 1 <br/> [String](../types/String.md) | The key | direct |
| [value](../slots/value.md) | 0..1 <br/> [Any](../classes/Any.md) | The value associated with the key | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [TransformationSpecification](../classes/TransformationSpecification.md) | [prefixes](../slots/prefixes.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ElementDerivation](../classes/ElementDerivation.md) | [value_mappings](../slots/value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ElementDerivation](../classes/ElementDerivation.md) | [expression_mappings](../slots/expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ElementDerivation](../classes/ElementDerivation.md) | [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ElementDerivation](../classes/ElementDerivation.md) | [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ClassDerivation](../classes/ClassDerivation.md) | [value_mappings](../slots/value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ClassDerivation](../classes/ClassDerivation.md) | [expression_mappings](../slots/expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ClassDerivation](../classes/ClassDerivation.md) | [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ClassDerivation](../classes/ClassDerivation.md) | [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ObjectDerivation](../classes/ObjectDerivation.md) | [value_mappings](../slots/value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ObjectDerivation](../classes/ObjectDerivation.md) | [expression_mappings](../slots/expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ObjectDerivation](../classes/ObjectDerivation.md) | [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [ObjectDerivation](../classes/ObjectDerivation.md) | [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [SlotDerivation](../classes/SlotDerivation.md) | [value_mappings](../slots/value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [SlotDerivation](../classes/SlotDerivation.md) | [expression_mappings](../slots/expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [SlotDerivation](../classes/SlotDerivation.md) | [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [SlotDerivation](../classes/SlotDerivation.md) | [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [EnumDerivation](../classes/EnumDerivation.md) | [value_mappings](../slots/value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [EnumDerivation](../classes/EnumDerivation.md) | [expression_mappings](../slots/expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [EnumDerivation](../classes/EnumDerivation.md) | [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [EnumDerivation](../classes/EnumDerivation.md) | [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md) | [value_mappings](../slots/value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md) | [expression_mappings](../slots/expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md) | [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md) | [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PrefixDerivation](../classes/PrefixDerivation.md) | [value_mappings](../slots/value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PrefixDerivation](../classes/PrefixDerivation.md) | [expression_mappings](../slots/expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PrefixDerivation](../classes/PrefixDerivation.md) | [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |
| [PrefixDerivation](../classes/PrefixDerivation.md) | [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | range | [KeyVal](../classes/KeyVal.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:KeyVal |
| native | linkmlmap:KeyVal |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: KeyVal
description: A generic key-value pair.
from_schema: https://w3id.org/linkml/transformer
attributes:
  key:
    name: key
    description: The key.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    key: true
    domain_of:
    - KeyVal
  value:
    name: value
    description: The value associated with the key.
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - SlotDerivation
    - KeyVal
    range: Any

```
</details>

### Induced

<details>
```yaml
name: KeyVal
description: A generic key-value pair.
from_schema: https://w3id.org/linkml/transformer
attributes:
  key:
    name: key
    description: The key.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    key: true
    owner: KeyVal
    domain_of:
    - KeyVal
    required: true
  value:
    name: value
    description: The value associated with the key.
    from_schema: https://w3id.org/linkml/transformer
    owner: KeyVal
    domain_of:
    - SlotDerivation
    - KeyVal
    range: Any

```
</details></div>