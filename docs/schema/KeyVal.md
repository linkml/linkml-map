---
search:
  boost: 10.0
---

# Class: KeyVal 


_A generic key-value pair._



<div data-search-exclude markdown="1">



URI: [linkmlmap:KeyVal](https://w3id.org/linkml/transformer/KeyVal)





```mermaid
 classDiagram
    class KeyVal
    click KeyVal href "../KeyVal/"
      KeyVal : key
        
      KeyVal : value
        
          
    
        
        
        KeyVal --> "0..1" Any : value
        click Any href "../Any/"
    

        
      
```




<!-- no inheritance hierarchy -->

## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [key](key.md) | 1 <br/> [String](String.md) | The key | direct |
| [value](value.md) | 0..1 <br/> [Any](Any.md) | The value associated with the key | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | [prefixes](prefixes.md) | range | [KeyVal](KeyVal.md) |
| [ElementDerivation](ElementDerivation.md) | [value_mappings](value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ElementDerivation](ElementDerivation.md) | [expression_mappings](expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ElementDerivation](ElementDerivation.md) | [expression_to_value_mappings](expression_to_value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ElementDerivation](ElementDerivation.md) | [expression_to_expression_mappings](expression_to_expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ClassDerivation](ClassDerivation.md) | [value_mappings](value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ClassDerivation](ClassDerivation.md) | [expression_mappings](expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ClassDerivation](ClassDerivation.md) | [expression_to_value_mappings](expression_to_value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ClassDerivation](ClassDerivation.md) | [expression_to_expression_mappings](expression_to_expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ObjectDerivation](ObjectDerivation.md) | [value_mappings](value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ObjectDerivation](ObjectDerivation.md) | [expression_mappings](expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ObjectDerivation](ObjectDerivation.md) | [expression_to_value_mappings](expression_to_value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [ObjectDerivation](ObjectDerivation.md) | [expression_to_expression_mappings](expression_to_expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [SlotDerivation](SlotDerivation.md) | [value_mappings](value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [SlotDerivation](SlotDerivation.md) | [expression_mappings](expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [SlotDerivation](SlotDerivation.md) | [expression_to_value_mappings](expression_to_value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [SlotDerivation](SlotDerivation.md) | [expression_to_expression_mappings](expression_to_expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [EnumDerivation](EnumDerivation.md) | [value_mappings](value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [EnumDerivation](EnumDerivation.md) | [expression_mappings](expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [EnumDerivation](EnumDerivation.md) | [expression_to_value_mappings](expression_to_value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [EnumDerivation](EnumDerivation.md) | [expression_to_expression_mappings](expression_to_expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | [value_mappings](value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | [expression_mappings](expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | [expression_to_value_mappings](expression_to_value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | [expression_to_expression_mappings](expression_to_expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PrefixDerivation](PrefixDerivation.md) | [value_mappings](value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PrefixDerivation](PrefixDerivation.md) | [expression_mappings](expression_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PrefixDerivation](PrefixDerivation.md) | [expression_to_value_mappings](expression_to_value_mappings.md) | range | [KeyVal](KeyVal.md) |
| [PrefixDerivation](PrefixDerivation.md) | [expression_to_expression_mappings](expression_to_expression_mappings.md) | range | [KeyVal](KeyVal.md) |












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