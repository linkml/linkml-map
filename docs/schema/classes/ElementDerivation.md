---
search:
  boost: 10.0
---

# Class: ElementDerivation 


_An abstract grouping for classes that provide a specification of how to derive a target element from a source element._



<div data-search-exclude markdown="1">


* __NOTE__: this is an abstract class and should not be instantiated directly


URI: [linkmlmap:class/ElementDerivation](https://w3id.org/linkml/transformer/class/ElementDerivation)





```mermaid
 classDiagram
    class ElementDerivation
    click ElementDerivation href "../../classes/ElementDerivation/"
      SpecificationComponent <|-- ElementDerivation
        click SpecificationComponent href "../../classes/SpecificationComponent/"
      

      ElementDerivation <|-- ClassDerivation
        click ClassDerivation href "../../classes/ClassDerivation/"
      ElementDerivation <|-- ObjectDerivation
        click ObjectDerivation href "../../classes/ObjectDerivation/"
      ElementDerivation <|-- SlotDerivation
        click SlotDerivation href "../../classes/SlotDerivation/"
      ElementDerivation <|-- EnumDerivation
        click EnumDerivation href "../../classes/EnumDerivation/"
      ElementDerivation <|-- PermissibleValueDerivation
        click PermissibleValueDerivation href "../../classes/PermissibleValueDerivation/"
      ElementDerivation <|-- PrefixDerivation
        click PrefixDerivation href "../../classes/PrefixDerivation/"
      

      ElementDerivation : comments
        
      ElementDerivation : copy_directives
        
          
    
        
        
        ElementDerivation --> "*" CopyDirective : copy_directives
        click CopyDirective href "../../classes/CopyDirective/"
    

        
      ElementDerivation : description
        
      ElementDerivation : expression_mappings
        
          
    
        
        
        ElementDerivation --> "*" KeyVal : expression_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ElementDerivation : expression_to_expression_mappings
        
          
    
        
        
        ElementDerivation --> "*" KeyVal : expression_to_expression_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ElementDerivation : expression_to_value_mappings
        
          
    
        
        
        ElementDerivation --> "*" KeyVal : expression_to_value_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ElementDerivation : implements
        
      ElementDerivation : is_a
        
          
    
        
        
        ElementDerivation --> "0..1" ElementDerivation : is_a
        click ElementDerivation href "../../classes/ElementDerivation/"
    

        
      ElementDerivation : mirror_source
        
      ElementDerivation : mixins
        
          
    
        
        
        ElementDerivation --> "*" ElementDerivation : mixins
        click ElementDerivation href "../../classes/ElementDerivation/"
    

        
      ElementDerivation : name
        
      ElementDerivation : overrides
        
          
    
        
        
        ElementDerivation --> "0..1" Any : overrides
        click Any href "../../classes/Any/"
    

        
      ElementDerivation : value_mappings
        
          
    
        
        
        ElementDerivation --> "*" KeyVal : value_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      
```





## Inheritance
* [SpecificationComponent](../classes/SpecificationComponent.md)
    * **ElementDerivation**
        * [ClassDerivation](../classes/ClassDerivation.md)
        * [ObjectDerivation](../classes/ObjectDerivation.md)
        * [SlotDerivation](../classes/SlotDerivation.md)
        * [EnumDerivation](../classes/EnumDerivation.md)
        * [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md)
        * [PrefixDerivation](../classes/PrefixDerivation.md)


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [name](../slots/name.md) | 1 <br/> [String](../types/String.md) | Name of the element in the target schema | direct |
| [copy_directives](../slots/copy_directives.md) | * <br/> [CopyDirective](../classes/CopyDirective.md) | Directives controlling which sub-elements of the source element are copied in... | direct |
| [overrides](../slots/overrides.md) | 0..1 <br/> [Any](../classes/Any.md) | overrides source schema slots | direct |
| [is_a](../slots/is_a.md) | 0..1 <br/> [ElementDerivation](../classes/ElementDerivation.md) | The parent element that the derived target element inherits from | direct |
| [mixins](../slots/mixins.md) | * <br/> [ElementDerivation](../classes/ElementDerivation.md) | Mixin elements applied to the derived target element | direct |
| [value_mappings](../slots/value_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table that is applied directly to mappings, in order of precedence | direct |
| [expression_mappings](../slots/expression_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table where the values are expressions evaluated against source bin... | direct |
| [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table in which the keys are boolean expressions and the values are ... | direct |
| [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table in which the keys and values are expressions | direct |
| [mirror_source](../slots/mirror_source.md) | 0..1 <br/> [Boolean](../types/Boolean.md) | If true, pass the source value through unchanged instead of transforming it | direct |
| [description](../slots/description.md) | 0..1 <br/> [String](../types/String.md) | description of the specification component | [SpecificationComponent](../classes/SpecificationComponent.md) |
| [implements](../slots/implements.md) | * <br/> [Uriorcurie](../types/Uriorcurie.md) | A reference to a specification that this component implements | [SpecificationComponent](../classes/SpecificationComponent.md) |
| [comments](../slots/comments.md) | * <br/> [String](../types/String.md) | A list of comments about this component | [SpecificationComponent](../classes/SpecificationComponent.md) |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [ElementDerivation](../classes/ElementDerivation.md) | [is_a](../slots/is_a.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [ElementDerivation](../classes/ElementDerivation.md) | [mixins](../slots/mixins.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [ClassDerivation](../classes/ClassDerivation.md) | [is_a](../slots/is_a.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [ClassDerivation](../classes/ClassDerivation.md) | [mixins](../slots/mixins.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [ObjectDerivation](../classes/ObjectDerivation.md) | [is_a](../slots/is_a.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [ObjectDerivation](../classes/ObjectDerivation.md) | [mixins](../slots/mixins.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [SlotDerivation](../classes/SlotDerivation.md) | [is_a](../slots/is_a.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [SlotDerivation](../classes/SlotDerivation.md) | [mixins](../slots/mixins.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [EnumDerivation](../classes/EnumDerivation.md) | [is_a](../slots/is_a.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [EnumDerivation](../classes/EnumDerivation.md) | [mixins](../slots/mixins.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md) | [is_a](../slots/is_a.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [PermissibleValueDerivation](../classes/PermissibleValueDerivation.md) | [mixins](../slots/mixins.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [PrefixDerivation](../classes/PrefixDerivation.md) | [is_a](../slots/is_a.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |
| [PrefixDerivation](../classes/PrefixDerivation.md) | [mixins](../slots/mixins.md) | range | [ElementDerivation](../classes/ElementDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:ElementDerivation |
| native | linkmlmap:ElementDerivation |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: ElementDerivation
description: An abstract grouping for classes that provide a specification of how
  to derive a target element from a source element.
from_schema: https://w3id.org/linkml/transformer
is_a: SpecificationComponent
abstract: true
attributes:
  name:
    name: name
    description: Name of the element in the target schema
    from_schema: https://w3id.org/linkml/transformer
    identifier: true
    domain_of:
    - SchemaReference
    - ElementDerivation
    - ClassDefault
    - ObjectDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    - Agent
  copy_directives:
    name: copy_directives
    description: Directives controlling which sub-elements of the source element are
      copied into the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - TransformationSpecification
    - ElementDerivation
    range: CopyDirective
    multivalued: true
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
    description: The parent element that the derived target element inherits from.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    domain_of:
    - ElementDerivation
    range: ElementDerivation
  mixins:
    name: mixins
    description: Mixin elements applied to the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:mixins
    domain_of:
    - ElementDerivation
    range: ElementDerivation
    multivalued: true
    inlined: false
  value_mappings:
    name: value_mappings
    description: A mapping table that is applied directly to mappings, in order of
      precedence. Keys should always be quoted in YAML to prevent type coercion —
      unquoted true/false become booleans and bare numbers become integers, which
      will not match the stringified source value used for lookup.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  expression_mappings:
    name: expression_mappings
    description: A mapping table where the values are expressions evaluated against
      source bindings. Looked up by the same key as value_mappings (the stringified
      source value). Keys should always be quoted (see value_mappings). If both value_mappings
      and expression_mappings are present, value_mappings takes precedence for keys
      that appear in both.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  expression_to_value_mappings:
    name: expression_to_value_mappings
    description: 'A mapping table in which the keys are boolean expressions and the
      values are literal results. On enum derivations, used for scalar binning: each
      key is evaluated with value() bound to the incoming value, and the first truthy
      key''s value is returned as the target permissible value. See issue #99.'
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  expression_to_expression_mappings:
    name: expression_to_expression_mappings
    description: A mapping table in which the keys and values are expressions
    deprecated: 'Deprecated: use case() with and/or operators instead (#127). Will
      be removed before 1.0.'
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  mirror_source:
    name: mirror_source
    description: If true, pass the source value through unchanged instead of transforming
      it.
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
  to derive a target element from a source element.
from_schema: https://w3id.org/linkml/transformer
is_a: SpecificationComponent
abstract: true
attributes:
  name:
    name: name
    description: Name of the element in the target schema
    from_schema: https://w3id.org/linkml/transformer
    identifier: true
    owner: ElementDerivation
    domain_of:
    - SchemaReference
    - ElementDerivation
    - ClassDefault
    - ObjectDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    - Agent
    required: true
  copy_directives:
    name: copy_directives
    description: Directives controlling which sub-elements of the source element are
      copied into the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    owner: ElementDerivation
    domain_of:
    - TransformationSpecification
    - ElementDerivation
    range: CopyDirective
    multivalued: true
    inlined: true
  overrides:
    name: overrides
    description: overrides source schema slots
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: Any
  is_a:
    name: is_a
    description: The parent element that the derived target element inherits from.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: ElementDerivation
  mixins:
    name: mixins
    description: Mixin elements applied to the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:mixins
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: ElementDerivation
    multivalued: true
    inlined: false
  value_mappings:
    name: value_mappings
    description: A mapping table that is applied directly to mappings, in order of
      precedence. Keys should always be quoted in YAML to prevent type coercion —
      unquoted true/false become booleans and bare numbers become integers, which
      will not match the stringified source value used for lookup.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  expression_mappings:
    name: expression_mappings
    description: A mapping table where the values are expressions evaluated against
      source bindings. Looked up by the same key as value_mappings (the stringified
      source value). Keys should always be quoted (see value_mappings). If both value_mappings
      and expression_mappings are present, value_mappings takes precedence for keys
      that appear in both.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  expression_to_value_mappings:
    name: expression_to_value_mappings
    description: 'A mapping table in which the keys are boolean expressions and the
      values are literal results. On enum derivations, used for scalar binning: each
      key is evaluated with value() bound to the incoming value, and the first truthy
      key''s value is returned as the target permissible value. See issue #99.'
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  expression_to_expression_mappings:
    name: expression_to_expression_mappings
    description: A mapping table in which the keys and values are expressions
    deprecated: 'Deprecated: use case() with and/or operators instead (#127). Will
      be removed before 1.0.'
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ElementDerivation
    domain_of:
    - ElementDerivation
    range: KeyVal
    multivalued: true
    inlined: true
  mirror_source:
    name: mirror_source
    description: If true, pass the source value through unchanged instead of transforming
      it.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
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
    owner: ElementDerivation
    domain_of:
    - SpecificationComponent
    range: string
  implements:
    name: implements
    description: A reference to a specification that this component implements.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ElementDerivation
    domain_of:
    - SpecificationComponent
    range: uriorcurie
    multivalued: true
  comments:
    name: comments
    description: A list of comments about this component. Comments are free text,
      and may be used to provide additional information about the component, including
      instructions for its use.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: rdfs:comment
    owner: ElementDerivation
    domain_of:
    - SpecificationComponent
    range: string
    multivalued: true

```
</details></div>