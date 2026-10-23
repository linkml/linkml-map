---
search:
  boost: 0.5
---

# Class: ObjectDerivation  <span style="color: red;"><strong> (DEPRECATED) </strong></span> 


_Deprecated. A nested derivation for constructing slot values that are class instances. Use list-based class_derivations instead._



<div data-search-exclude markdown="1">



URI: [linkmlmap:class/ObjectDerivation](https://w3id.org/linkml/transformer/class/ObjectDerivation)





```mermaid
 classDiagram
    class ObjectDerivation
    click ObjectDerivation href "../../classes/ObjectDerivation/"
      ElementDerivation <|-- ObjectDerivation
        click ElementDerivation href "../../classes/ElementDerivation/"
      
      ObjectDerivation : class_derivations
        
          
    
        
        
        ObjectDerivation --> "*" ClassDerivation : class_derivations
        click ClassDerivation href "../../classes/ClassDerivation/"
    

        
      ObjectDerivation : comments
        
      ObjectDerivation : copy_directives
        
          
    
        
        
        ObjectDerivation --> "*" CopyDirective : copy_directives
        click CopyDirective href "../../classes/CopyDirective/"
    

        
      ObjectDerivation : description
        
      ObjectDerivation : expression_mappings
        
          
    
        
        
        ObjectDerivation --> "*" KeyVal : expression_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ObjectDerivation : expression_to_expression_mappings
        
          
    
        
        
        ObjectDerivation --> "*" KeyVal : expression_to_expression_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ObjectDerivation : expression_to_value_mappings
        
          
    
        
        
        ObjectDerivation --> "*" KeyVal : expression_to_value_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ObjectDerivation : implements
        
      ObjectDerivation : is_a
        
          
    
        
        
        ObjectDerivation --> "0..1" ElementDerivation : is_a
        click ElementDerivation href "../../classes/ElementDerivation/"
    

        
      ObjectDerivation : mirror_source
        
      ObjectDerivation : mixins
        
          
    
        
        
        ObjectDerivation --> "*" ElementDerivation : mixins
        click ElementDerivation href "../../classes/ElementDerivation/"
    

        
      ObjectDerivation : name
        
      ObjectDerivation : overrides
        
          
    
        
        
        ObjectDerivation --> "0..1" Any : overrides
        click Any href "../../classes/Any/"
    

        
      ObjectDerivation : value_mappings
        
          
    
        
        
        ObjectDerivation --> "*" KeyVal : value_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      
```





## Inheritance
* [SpecificationComponent](../classes/SpecificationComponent.md)
    * [ElementDerivation](../classes/ElementDerivation.md)
        * **ObjectDerivation**


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [name](../slots/name.md) | 0..1 <br/> [String](../types/String.md) | Name of the element in the target schema | direct |
| [class_derivations](../slots/class_derivations.md) | * <br/> [ClassDerivation](../classes/ClassDerivation.md) | Class derivations used to construct nested instances for this (deprecated) ob... | direct |
| [copy_directives](../slots/copy_directives.md) | * <br/> [CopyDirective](../classes/CopyDirective.md) | Directives controlling which sub-elements of the source element are copied in... | [ElementDerivation](../classes/ElementDerivation.md) |
| [overrides](../slots/overrides.md) | 0..1 <br/> [Any](../classes/Any.md) | overrides source schema slots | [ElementDerivation](../classes/ElementDerivation.md) |
| [is_a](../slots/is_a.md) | 0..1 <br/> [ElementDerivation](../classes/ElementDerivation.md) | The parent element that the derived target element inherits from | [ElementDerivation](../classes/ElementDerivation.md) |
| [mixins](../slots/mixins.md) | * <br/> [ElementDerivation](../classes/ElementDerivation.md) | Mixin elements applied to the derived target element | [ElementDerivation](../classes/ElementDerivation.md) |
| [value_mappings](../slots/value_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table that is applied directly to mappings, in order of precedence | [ElementDerivation](../classes/ElementDerivation.md) |
| [expression_mappings](../slots/expression_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table where the values are expressions evaluated against source bin... | [ElementDerivation](../classes/ElementDerivation.md) |
| [expression_to_value_mappings](../slots/expression_to_value_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table in which the keys are boolean expressions and the values are ... | [ElementDerivation](../classes/ElementDerivation.md) |
| [expression_to_expression_mappings](../slots/expression_to_expression_mappings.md) | * <br/> [KeyVal](../classes/KeyVal.md) | A mapping table in which the keys and values are expressions | [ElementDerivation](../classes/ElementDerivation.md) |
| [mirror_source](../slots/mirror_source.md) | 0..1 <br/> [Boolean](../types/Boolean.md) | If true, pass the source value through unchanged instead of transforming it | [ElementDerivation](../classes/ElementDerivation.md) |
| [description](../slots/description.md) | 0..1 <br/> [String](../types/String.md) | description of the specification component | [SpecificationComponent](../classes/SpecificationComponent.md) |
| [implements](../slots/implements.md) | * <br/> [Uriorcurie](../types/Uriorcurie.md) | A reference to a specification that this component implements | [SpecificationComponent](../classes/SpecificationComponent.md) |
| [comments](../slots/comments.md) | * <br/> [String](../types/String.md) | A list of comments about this component | [SpecificationComponent](../classes/SpecificationComponent.md) |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [SlotDerivation](../classes/SlotDerivation.md) | [object_derivations](../slots/object_derivations.md) | range | [ObjectDerivation](../classes/ObjectDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:ObjectDerivation |
| native | linkmlmap:ObjectDerivation |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: ObjectDerivation
description: Deprecated. A nested derivation for constructing slot values that are
  class instances. Use list-based class_derivations instead.
deprecated: Use list-based class_derivations instead of nesting via object_derivations.
  See https://github.com/linkml/linkml-map/issues/112
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  name:
    name: name
    description: Name of the element in the target schema
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - SchemaReference
    - ElementDerivation
    - ClassDefault
    - ObjectDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    - Agent
    required: false
  class_derivations:
    name: class_derivations
    description: Class derivations used to construct nested instances for this (deprecated)
      object derivation.
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - TransformationSpecification
    - ObjectDerivation
    - SlotDerivation
    range: ClassDerivation
    multivalued: true
    inlined: true

```
</details>

### Induced

<details>
```yaml
name: ObjectDerivation
description: Deprecated. A nested derivation for constructing slot values that are
  class instances. Use list-based class_derivations instead.
deprecated: Use list-based class_derivations instead of nesting via object_derivations.
  See https://github.com/linkml/linkml-map/issues/112
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  name:
    name: name
    description: Name of the element in the target schema
    from_schema: https://w3id.org/linkml/transformer
    owner: ObjectDerivation
    domain_of:
    - SchemaReference
    - ElementDerivation
    - ClassDefault
    - ObjectDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    - Agent
    required: false
  class_derivations:
    name: class_derivations
    description: Class derivations used to construct nested instances for this (deprecated)
      object derivation.
    from_schema: https://w3id.org/linkml/transformer
    owner: ObjectDerivation
    domain_of:
    - TransformationSpecification
    - ObjectDerivation
    - SlotDerivation
    range: ClassDerivation
    multivalued: true
    inlined: true
  copy_directives:
    name: copy_directives
    description: Directives controlling which sub-elements of the source element are
      copied into the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    owner: ObjectDerivation
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
    owner: ObjectDerivation
    domain_of:
    - ElementDerivation
    range: Any
  is_a:
    name: is_a
    description: The parent element that the derived target element inherits from.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    owner: ObjectDerivation
    domain_of:
    - ElementDerivation
    range: ElementDerivation
  mixins:
    name: mixins
    description: Mixin elements applied to the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:mixins
    owner: ObjectDerivation
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
    owner: ObjectDerivation
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
    owner: ObjectDerivation
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
    owner: ObjectDerivation
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
    owner: ObjectDerivation
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
    owner: ObjectDerivation
    domain_of:
    - ElementDerivation
    range: boolean
  description:
    name: description
    description: description of the specification component
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: dcterms:description
    owner: ObjectDerivation
    domain_of:
    - SpecificationComponent
    range: string
  implements:
    name: implements
    description: A reference to a specification that this component implements.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ObjectDerivation
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
    owner: ObjectDerivation
    domain_of:
    - SpecificationComponent
    range: string
    multivalued: true

```
</details></div>