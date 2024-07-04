

# Class: ElementDerivation


_An abstract grouping for classes that provide a specification of how to  derive a target element from a source element._




* __NOTE__: this is an abstract class and should not be instantiated directly


URI: [linkmltr:ElementDerivation](https://w3id.org/linkml/transformer/ElementDerivation)




```mermaid
 classDiagram
    class ElementDerivation
      SpecificationComponent <|-- ElementDerivation
      

      ElementDerivation <|-- ClassDerivation
      ElementDerivation <|-- SlotDerivation
      ElementDerivation <|-- EnumDerivation
      ElementDerivation <|-- PermissibleValueDerivation
      ElementDerivation <|-- PrefixDerivation
      
      
      ElementDerivation : comments
        
      ElementDerivation : copy_directives
        
          ElementDerivation --> CopyDirective : copy_directives
        
      ElementDerivation : description
        
          ElementDerivation --> None : description
        
      ElementDerivation : expression_to_expression_mappings
        
          ElementDerivation --> KeyVal : expression_to_expression_mappings
        
      ElementDerivation : expression_to_value_mappings
        
          ElementDerivation --> KeyVal : expression_to_value_mappings
        
      ElementDerivation : implements
        
      ElementDerivation : is_a
        
          ElementDerivation --> ElementDerivation : is_a
        
      ElementDerivation : mirror_source
        
      ElementDerivation : mixins
        
          ElementDerivation --> ElementDerivation : mixins
        
      ElementDerivation : name
        
          ElementDerivation --> None : name
        
      ElementDerivation : overrides
        
          ElementDerivation --> Any : overrides
        
      ElementDerivation : value_mappings
        
          ElementDerivation --> KeyVal : value_mappings
        
      
```





## Inheritance
* [SpecificationComponent](SpecificationComponent.md)
    * **ElementDerivation**
        * [ClassDerivation](ClassDerivation.md)
        * [SlotDerivation](SlotDerivation.md)
        * [EnumDerivation](EnumDerivation.md)
        * [PermissibleValueDerivation](PermissibleValueDerivation.md)
        * [PrefixDerivation](PrefixDerivation.md)



## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [name](name.md) | 0..1 <br/> [String](String.md) | Name of the element in the target schema | direct |
| [copy_directives](copy_directives.md) | 0..* <br/> [CopyDirective](CopyDirective.md) |  | direct |
| [overrides](overrides.md) | 0..1 <br/> [Any](Any.md) | overrides source schema slots | direct |
| [is_a](is_a.md) | 0..1 <br/> [ElementDerivation](ElementDerivation.md) |  | direct |
| [mixins](mixins.md) | 0..* <br/> [ElementDerivation](ElementDerivation.md) |  | direct |
| [value_mappings](value_mappings.md) | 0..* <br/> [KeyVal](KeyVal.md) | A mapping table that is applied directly to mappings, in order of precedence | direct |
| [expression_to_value_mappings](expression_to_value_mappings.md) | 0..* <br/> [KeyVal](KeyVal.md) | A mapping table in which the keys are expressions | direct |
| [expression_to_expression_mappings](expression_to_expression_mappings.md) | 0..* <br/> [KeyVal](KeyVal.md) | A mapping table in which the keys and values are expressions | direct |
| [mirror_source](mirror_source.md) | 0..1 <br/> [Boolean](Boolean.md) |  | direct |
| [description](description.md) | 0..1 <br/> [String](String.md) | description of the specification component | [SpecificationComponent](SpecificationComponent.md) |
| [implements](implements.md) | 0..* <br/> [Uriorcurie](Uriorcurie.md) | A reference to a specification that this component implements | [SpecificationComponent](SpecificationComponent.md) |
| [comments](comments.md) | 0..* <br/> [String](String.md) | A list of comments about this component | [SpecificationComponent](SpecificationComponent.md) |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [ElementDerivation](ElementDerivation.md) | [is_a](is_a.md) | range | [ElementDerivation](ElementDerivation.md) |
| [ElementDerivation](ElementDerivation.md) | [mixins](mixins.md) | range | [ElementDerivation](ElementDerivation.md) |
| [ClassDerivation](ClassDerivation.md) | [is_a](is_a.md) | range | [ElementDerivation](ElementDerivation.md) |
| [ClassDerivation](ClassDerivation.md) | [mixins](mixins.md) | range | [ElementDerivation](ElementDerivation.md) |
| [SlotDerivation](SlotDerivation.md) | [is_a](is_a.md) | range | [ElementDerivation](ElementDerivation.md) |
| [SlotDerivation](SlotDerivation.md) | [mixins](mixins.md) | range | [ElementDerivation](ElementDerivation.md) |
| [EnumDerivation](EnumDerivation.md) | [is_a](is_a.md) | range | [ElementDerivation](ElementDerivation.md) |
| [EnumDerivation](EnumDerivation.md) | [mixins](mixins.md) | range | [ElementDerivation](ElementDerivation.md) |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | [is_a](is_a.md) | range | [ElementDerivation](ElementDerivation.md) |
| [PermissibleValueDerivation](PermissibleValueDerivation.md) | [mixins](mixins.md) | range | [ElementDerivation](ElementDerivation.md) |
| [PrefixDerivation](PrefixDerivation.md) | [is_a](is_a.md) | range | [ElementDerivation](ElementDerivation.md) |
| [PrefixDerivation](PrefixDerivation.md) | [mixins](mixins.md) | range | [ElementDerivation](ElementDerivation.md) |






## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer





## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmltr:ElementDerivation |
| native | linkmltr:ElementDerivation |





## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: ElementDerivation
description: An abstract grouping for classes that provide a specification of how
  to  derive a target element from a source element.
from_schema: https://w3id.org/linkml/transformer
is_a: SpecificationComponent
abstract: true
attributes:
  name:
    name: name
    description: Name of the element in the target schema
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    key: true
    domain_of:
    - ElementDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    required: true
  copy_directives:
    name: copy_directives
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    domain_of:
    - ElementDerivation
    range: CopyDirective
    inlined: true
  overrides:
    name: overrides
    description: overrides source schema slots
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ElementDerivation
    range: Any
  is_a:
    name: is_a
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    domain_of:
    - ElementDerivation
    range: ElementDerivation
  mixins:
    name: mixins
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:mixins
    multivalued: true
    domain_of:
    - ElementDerivation
    range: ElementDerivation
    inlined: false
  value_mappings:
    name: value_mappings
    description: A mapping table that is applied directly to mappings, in order of
      precedence
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    domain_of:
    - ElementDerivation
    range: KeyVal
    inlined: true
  expression_to_value_mappings:
    name: expression_to_value_mappings
    description: A mapping table in which the keys are expressions
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    domain_of:
    - ElementDerivation
    range: KeyVal
    inlined: true
  expression_to_expression_mappings:
    name: expression_to_expression_mappings
    description: A mapping table in which the keys and values are expressions
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    domain_of:
    - ElementDerivation
    range: KeyVal
    inlined: true
  mirror_source:
    name: mirror_source
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ElementDerivation
    range: boolean

```
</details>

### Induced

<details>
```yaml
name: ElementDerivation
description: An abstract grouping for classes that provide a specification of how
  to  derive a target element from a source element.
from_schema: https://w3id.org/linkml/transformer
is_a: SpecificationComponent
abstract: true
attributes:
  name:
    name: name
    description: Name of the element in the target schema
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    key: true
    alias: name
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    required: true
  copy_directives:
    name: copy_directives
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    alias: copy_directives
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: CopyDirective
    inlined: true
  overrides:
    name: overrides
    description: overrides source schema slots
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: overrides
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: Any
  is_a:
    name: is_a
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    alias: is_a
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: ElementDerivation
  mixins:
    name: mixins
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:mixins
    multivalued: true
    alias: mixins
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: ElementDerivation
    inlined: false
  value_mappings:
    name: value_mappings
    description: A mapping table that is applied directly to mappings, in order of
      precedence
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    alias: value_mappings
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    inlined: true
  expression_to_value_mappings:
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
  expression_to_expression_mappings:
    name: expression_to_expression_mappings
    description: A mapping table in which the keys and values are expressions
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    alias: expression_to_expression_mappings
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    inlined: true
  mirror_source:
    name: mirror_source
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: mirror_source
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: boolean
  description:
    name: description
    description: description of the specification component
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: dcterms:description
    alias: description
    owner: ElementDerivation
    domain_of:
    - SpecificationComponent
    range: string
  implements:
    name: implements
    description: A reference to a specification that this component implements.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    alias: implements
    owner: ElementDerivation
    domain_of:
    - SpecificationComponent
    range: uriorcurie
  comments:
    name: comments
    description: A list of comments about this component. Comments are free text,
      and may be used to provide additional information about the component, including
      instructions for its use.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: rdfs:comment
    multivalued: true
    alias: comments
    owner: ElementDerivation
    domain_of:
    - SpecificationComponent
    range: string

```
</details>