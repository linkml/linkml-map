---
search:
  boost: 10.0
---

# Class: StringificationConfiguration 


_Configuration for collapsing multiple values into a single delimited or serialized string value._



<div data-search-exclude markdown="1">



URI: [linkmlmap:class/StringificationConfiguration](https://w3id.org/linkml/transformer/class/StringificationConfiguration)





```mermaid
 classDiagram
    class StringificationConfiguration
    click StringificationConfiguration href "../../classes/StringificationConfiguration/"
      StringificationConfiguration : delimiter
        
      StringificationConfiguration : over_slots
        
      StringificationConfiguration : reversed
        
      StringificationConfiguration : syntax
        
          
    
        
        
        StringificationConfiguration --> "0..1" SerializationSyntaxType : syntax
        click SerializationSyntaxType href "../../enums/SerializationSyntaxType/"
    

        
      
```




<!-- no inheritance hierarchy -->

## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [delimiter](../slots/delimiter.md) | 0..1 <br/> [String](../types/String.md) | Delimiter used to join multiple values into a single string | direct |
| [reversed](../slots/reversed.md) | 0..1 <br/> [Boolean](../types/Boolean.md) | If true, reverse the operation, splitting a delimited or serialized string ba... | direct |
| [over_slots](../slots/over_slots.md) | * <br/> [String](../types/String.md) | The source slots whose values are combined into the stringified result | direct |
| [syntax](../slots/syntax.md) | 0..1 <br/> [SerializationSyntaxType](../enums/SerializationSyntaxType.md) | Serialization syntax used to stringify the values when no delimiter is given | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [SlotDerivation](../classes/SlotDerivation.md) | [stringification](../slots/stringification.md) | range | [StringificationConfiguration](../classes/StringificationConfiguration.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:StringificationConfiguration |
| native | linkmlmap:StringificationConfiguration |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: StringificationConfiguration
description: Configuration for collapsing multiple values into a single delimited
  or serialized string value.
from_schema: https://w3id.org/linkml/transformer
attributes:
  delimiter:
    name: delimiter
    description: Delimiter used to join multiple values into a single string.
    examples:
    - value: ','
    - value: '|'
    - value: ;
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - StringificationConfiguration
    range: string
  reversed:
    name: reversed
    description: If true, reverse the operation, splitting a delimited or serialized
      string back into multiple values.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - StringificationConfiguration
    range: boolean
  over_slots:
    name: over_slots
    description: The source slots whose values are combined into the stringified result.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - StringificationConfiguration
    range: string
    multivalued: true
  syntax:
    name: syntax
    description: Serialization syntax used to stringify the values when no delimiter
      is given.
    examples:
    - value: json
    - value: yaml
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - StringificationConfiguration
    range: SerializationSyntaxType

```
</details>

### Induced

<details>
```yaml
name: StringificationConfiguration
description: Configuration for collapsing multiple values into a single delimited
  or serialized string value.
from_schema: https://w3id.org/linkml/transformer
attributes:
  delimiter:
    name: delimiter
    description: Delimiter used to join multiple values into a single string.
    examples:
    - value: ','
    - value: '|'
    - value: ;
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: StringificationConfiguration
    domain_of:
    - StringificationConfiguration
    range: string
  reversed:
    name: reversed
    description: If true, reverse the operation, splitting a delimited or serialized
      string back into multiple values.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: StringificationConfiguration
    domain_of:
    - StringificationConfiguration
    range: boolean
  over_slots:
    name: over_slots
    description: The source slots whose values are combined into the stringified result.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: StringificationConfiguration
    domain_of:
    - StringificationConfiguration
    range: string
    multivalued: true
  syntax:
    name: syntax
    description: Serialization syntax used to stringify the values when no delimiter
      is given.
    examples:
    - value: json
    - value: yaml
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: StringificationConfiguration
    domain_of:
    - StringificationConfiguration
    range: SerializationSyntaxType

```
</details></div>