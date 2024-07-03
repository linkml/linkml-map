

# Class: PermissibleValueDerivation


_A specification of how to derive the value of a PV from a source enum_





URI: [linkmltr:PermissibleValueDerivation](https://w3id.org/linkml/transformer/PermissibleValueDerivation)




```mermaid
 classDiagram
    class PermissibleValueDerivation
      ElementDerivation <|-- PermissibleValueDerivation
      
      PermissibleValueDerivation : comments
        
      PermissibleValueDerivation : copy_directives
        
          PermissibleValueDerivation --> CopyDirective : copy_directives
        
      PermissibleValueDerivation : description
        
          PermissibleValueDerivation --> None : description
        
      PermissibleValueDerivation : expr
        
      PermissibleValueDerivation : expression_to_expression_mappings
        
          PermissibleValueDerivation --> KeyVal : expression_to_expression_mappings
        
      PermissibleValueDerivation : expression_to_value_mappings
        
          PermissibleValueDerivation --> KeyVal : expression_to_value_mappings
        
      PermissibleValueDerivation : hide
        
      PermissibleValueDerivation : implements
        
      PermissibleValueDerivation : is_a
        
          PermissibleValueDerivation --> ElementDerivation : is_a
        
      PermissibleValueDerivation : mirror_source
        
      PermissibleValueDerivation : mixins
        
          PermissibleValueDerivation --> ElementDerivation : mixins
        
      PermissibleValueDerivation : name
        
          PermissibleValueDerivation --> None : name
        
      PermissibleValueDerivation : overrides
        
          PermissibleValueDerivation --> Any : overrides
        
      PermissibleValueDerivation : populated_from
        
      PermissibleValueDerivation : sources
        
      PermissibleValueDerivation : value_mappings
        
          PermissibleValueDerivation --> KeyVal : value_mappings
        
      
```





## Inheritance
* [SpecificationComponent](SpecificationComponent.md)
    * [ElementDerivation](ElementDerivation.md)
        * **PermissibleValueDerivation**



## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [name](name.md) | 0..1 <br/> [String](String.md) | Target permissible value text | direct |
| [expr](expr.md) | 0..1 <br/> [String](String.md) |  | direct |
| [populated_from](populated_from.md) | 0..1 <br/> [String](String.md) | Source permissible value | direct |
| [sources](sources.md) | 0..* <br/> [String](String.md) |  | direct |
| [hide](hide.md) | 0..1 <br/> [Boolean](Boolean.md) |  | direct |
| [copy_directives](copy_directives.md) | 0..* <br/> [CopyDirective](CopyDirective.md) |  | [ElementDerivation](ElementDerivation.md) |
| [overrides](overrides.md) | 0..1 <br/> [Any](Any.md) | overrides source schema slots | [ElementDerivation](ElementDerivation.md) |
| [is_a](is_a.md) | 0..1 <br/> [ElementDerivation](ElementDerivation.md) |  | [ElementDerivation](ElementDerivation.md) |
| [mixins](mixins.md) | 0..* <br/> [ElementDerivation](ElementDerivation.md) |  | [ElementDerivation](ElementDerivation.md) |
| [value_mappings](value_mappings.md) | 0..* <br/> [KeyVal](KeyVal.md) | A mapping table that is applied directly to mappings, in order of precedence | [ElementDerivation](ElementDerivation.md) |
| [expression_to_value_mappings](expression_to_value_mappings.md) | 0..* <br/> [KeyVal](KeyVal.md) | A mapping table in which the keys are expressions | [ElementDerivation](ElementDerivation.md) |
| [expression_to_expression_mappings](expression_to_expression_mappings.md) | 0..* <br/> [KeyVal](KeyVal.md) | A mapping table in which the keys and values are expressions | [ElementDerivation](ElementDerivation.md) |
| [mirror_source](mirror_source.md) | 0..1 <br/> [Boolean](Boolean.md) |  | [ElementDerivation](ElementDerivation.md) |
| [description](description.md) | 0..1 <br/> [String](String.md) | description of the specification component | [SpecificationComponent](SpecificationComponent.md) |
| [implements](implements.md) | 0..* <br/> [Uriorcurie](Uriorcurie.md) | A reference to a specification that this component implements | [SpecificationComponent](SpecificationComponent.md) |
| [comments](comments.md) | 0..* <br/> [String](String.md) | A list of comments about this component | [SpecificationComponent](SpecificationComponent.md) |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [EnumDerivation](EnumDerivation.md) | [permissible_value_derivations](permissible_value_derivations.md) | range | [PermissibleValueDerivation](PermissibleValueDerivation.md) |






## TODOs

* this is currently under-specified. We will need boolean combinators to express if-then-else

## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer





## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmltr:PermissibleValueDerivation |
| native | linkmltr:PermissibleValueDerivation |





## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: PermissibleValueDerivation
description: A specification of how to derive the value of a PV from a source enum
todos:
- this is currently under-specified. We will need boolean combinators to express if-then-else
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  name:
    name: name
    description: Target permissible value text
    from_schema: https://w3id.org/linkml/transformer
    key: true
    domain_of:
    - ElementDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    required: true
  expr:
    name: expr
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  populated_from:
    name: populated_from
    description: Source permissible value
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  sources:
    name: sources
    from_schema: https://w3id.org/linkml/transformer
    multivalued: true
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  hide:
    name: hide
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: boolean

```
</details>

### Induced

<details>
```yaml
name: PermissibleValueDerivation
description: A specification of how to derive the value of a PV from a source enum
todos:
- this is currently under-specified. We will need boolean combinators to express if-then-else
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  name:
    name: name
    description: Target permissible value text
    from_schema: https://w3id.org/linkml/transformer
    key: true
    alias: name
    owner: PermissibleValueDerivation
    domain_of:
    - ElementDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    required: true
  expr:
    name: expr
    from_schema: https://w3id.org/linkml/transformer
    alias: expr
    owner: PermissibleValueDerivation
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  populated_from:
    name: populated_from
    description: Source permissible value
    from_schema: https://w3id.org/linkml/transformer
    alias: populated_from
    owner: PermissibleValueDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  sources:
    name: sources
    from_schema: https://w3id.org/linkml/transformer
    multivalued: true
    alias: sources
    owner: PermissibleValueDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  hide:
    name: hide
    from_schema: https://w3id.org/linkml/transformer
    alias: hide
    owner: PermissibleValueDerivation
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: boolean
  copy_directives:
    name: copy_directives
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    alias: copy_directives
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
    domain_of:
    - ElementDerivation
    range: Any
  is_a:
    name: is_a
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    alias: is_a
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    inlined: true
  mirror_source:
    name: mirror_source
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: mirror_source
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
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
    owner: PermissibleValueDerivation
    domain_of:
    - SpecificationComponent
    range: string

```
</details>