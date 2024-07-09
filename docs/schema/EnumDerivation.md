

# Class: EnumDerivation


_A specification of how to derive the value of a target enum from a source enum_





URI: [linkmltr:EnumDerivation](https://w3id.org/linkml/transformer/EnumDerivation)




```mermaid
 classDiagram
    class EnumDerivation
      ElementDerivation <|-- EnumDerivation
      
      EnumDerivation : comments
        
      EnumDerivation : copy_directives
        
          EnumDerivation --> CopyDirective : copy_directives
        
      EnumDerivation : description
        
          EnumDerivation --> None : description
        
      EnumDerivation : expr
        
      EnumDerivation : expression_to_expression_mappings
        
          EnumDerivation --> KeyVal : expression_to_expression_mappings
        
      EnumDerivation : expression_to_value_mappings
        
          EnumDerivation --> KeyVal : expression_to_value_mappings
        
      EnumDerivation : hide
        
      EnumDerivation : implements
        
      EnumDerivation : is_a
        
          EnumDerivation --> ElementDerivation : is_a
        
      EnumDerivation : mirror_source
        
      EnumDerivation : mixins
        
          EnumDerivation --> ElementDerivation : mixins
        
      EnumDerivation : name
        
          EnumDerivation --> None : name
        
      EnumDerivation : overrides
        
          EnumDerivation --> Any : overrides
        
      EnumDerivation : permissible_value_derivations
        
          EnumDerivation --> PermissibleValueDerivation : permissible_value_derivations
        
      EnumDerivation : populated_from
        
      EnumDerivation : sources
        
      EnumDerivation : value_mappings
        
          EnumDerivation --> KeyVal : value_mappings
        
      
```





## Inheritance
* [SpecificationComponent](SpecificationComponent.md)
    * [ElementDerivation](ElementDerivation.md)
        * **EnumDerivation**



## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [name](name.md) | 0..1 <br/> [String](String.md) | Target enum name | direct |
| [populated_from](populated_from.md) | 0..1 <br/> [EnumReference](EnumReference.md) | Source enum name | direct |
| [sources](sources.md) | 0..* <br/> [EnumReference](EnumReference.md) |  | direct |
| [expr](expr.md) | 0..1 <br/> [String](String.md) | An expression to be evaluated on the source object to derive the target slot | direct |
| [hide](hide.md) | 0..1 <br/> [Boolean](Boolean.md) | True if this is suppressed | direct |
| [permissible_value_derivations](permissible_value_derivations.md) | 0..* <br/> [PermissibleValueDerivation](PermissibleValueDerivation.md) | Instructions on how to derive a set of PVs in the target schema | direct |
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
| [TransformationSpecification](TransformationSpecification.md) | [enum_derivations](enum_derivations.md) | range | [EnumDerivation](EnumDerivation.md) |






## Identifier and Mapping Information







### Schema Source


* from schema: https://w3id.org/linkml/transformer





## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmltr:EnumDerivation |
| native | linkmltr:EnumDerivation |





## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: EnumDerivation
description: A specification of how to derive the value of a target enum from a source
  enum
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  name:
    name: name
    description: Target enum name
    from_schema: https://w3id.org/linkml/transformer
    key: true
    domain_of:
    - ElementDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    required: true
  populated_from:
    name: populated_from
    description: Source enum name
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: EnumReference
  sources:
    name: sources
    from_schema: https://w3id.org/linkml/transformer
    multivalued: true
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: EnumReference
  expr:
    name: expr
    description: An expression to be evaluated on the source object to derive the
      target slot. Should be specified using the LinkML expression language.
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  hide:
    name: hide
    description: True if this is suppressed
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: boolean
  permissible_value_derivations:
    name: permissible_value_derivations
    description: Instructions on how to derive a set of PVs in the target schema
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    domain_of:
    - EnumDerivation
    range: PermissibleValueDerivation
    inlined: true

```
</details>

### Induced

<details>
```yaml
name: EnumDerivation
description: A specification of how to derive the value of a target enum from a source
  enum
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  name:
    name: name
    description: Target enum name
    from_schema: https://w3id.org/linkml/transformer
    key: true
    alias: name
    owner: EnumDerivation
    domain_of:
    - ElementDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    required: true
  populated_from:
    name: populated_from
    description: Source enum name
    from_schema: https://w3id.org/linkml/transformer
    alias: populated_from
    owner: EnumDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: EnumReference
  sources:
    name: sources
    from_schema: https://w3id.org/linkml/transformer
    multivalued: true
    alias: sources
    owner: EnumDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: EnumReference
  expr:
    name: expr
    description: An expression to be evaluated on the source object to derive the
      target slot. Should be specified using the LinkML expression language.
    from_schema: https://w3id.org/linkml/transformer
    alias: expr
    owner: EnumDerivation
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: string
  hide:
    name: hide
    description: True if this is suppressed
    from_schema: https://w3id.org/linkml/transformer
    alias: hide
    owner: EnumDerivation
    domain_of:
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: boolean
  permissible_value_derivations:
    name: permissible_value_derivations
    description: Instructions on how to derive a set of PVs in the target schema
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    alias: permissible_value_derivations
    owner: EnumDerivation
    domain_of:
    - EnumDerivation
    range: PermissibleValueDerivation
    inlined: true
  copy_directives:
    name: copy_directives
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    multivalued: true
    alias: copy_directives
    owner: EnumDerivation
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
    owner: EnumDerivation
    domain_of:
    - ElementDerivation
    range: Any
  is_a:
    name: is_a
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    alias: is_a
    owner: EnumDerivation
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
    owner: EnumDerivation
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
    owner: EnumDerivation
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
    owner: EnumDerivation
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
    owner: EnumDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    inlined: true
  mirror_source:
    name: mirror_source
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    alias: mirror_source
    owner: EnumDerivation
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
    owner: EnumDerivation
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
    owner: EnumDerivation
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
    owner: EnumDerivation
    domain_of:
    - SpecificationComponent
    range: string

```
</details>