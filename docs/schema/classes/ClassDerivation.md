---
search:
  boost: 10.0
---

# Class: ClassDerivation 


_A specification of how to derive a target class from a source class._



<div data-search-exclude markdown="1">



URI: [linkmlmap:class/ClassDerivation](https://w3id.org/linkml/transformer/class/ClassDerivation)





```mermaid
 classDiagram
    class ClassDerivation
    click ClassDerivation href "../../classes/ClassDerivation/"
      ElementDerivation <|-- ClassDerivation
        click ElementDerivation href "../../classes/ElementDerivation/"
      
      ClassDerivation : comments
        
      ClassDerivation : copy_directives
        
          
    
        
        
        ClassDerivation --> "*" CopyDirective : copy_directives
        click CopyDirective href "../../classes/CopyDirective/"
    

        
      ClassDerivation : description
        
      ClassDerivation : expression_mappings
        
          
    
        
        
        ClassDerivation --> "*" KeyVal : expression_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ClassDerivation : expression_to_expression_mappings
        
          
    
        
        
        ClassDerivation --> "*" KeyVal : expression_to_expression_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ClassDerivation : expression_to_value_mappings
        
          
    
        
        
        ClassDerivation --> "*" KeyVal : expression_to_value_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      ClassDerivation : implements
        
      ClassDerivation : is_a
        
          
    
        
        
        ClassDerivation --> "0..1" ElementDerivation : is_a
        click ElementDerivation href "../../classes/ElementDerivation/"
    

        
      ClassDerivation : joins
        
          
    
        
        
        ClassDerivation --> "*" AliasedClass : joins
        click AliasedClass href "../../classes/AliasedClass/"
    

        
      ClassDerivation : mint_ids
        
      ClassDerivation : mirror_source
        
      ClassDerivation : mixins
        
          
    
        
        
        ClassDerivation --> "*" ElementDerivation : mixins
        click ElementDerivation href "../../classes/ElementDerivation/"
    

        
      ClassDerivation : name
        
      ClassDerivation : overrides
        
          
    
        
        
        ClassDerivation --> "0..1" Any : overrides
        click Any href "../../classes/Any/"
    

        
      ClassDerivation : pivot_operation
        
          
    
        
        
        ClassDerivation --> "0..1" PivotOperation : pivot_operation
        click PivotOperation href "../../classes/PivotOperation/"
    

        
      ClassDerivation : populated_from
        
      ClassDerivation : slot_derivations
        
          
    
        
        
        ClassDerivation --> "*" SlotDerivation : slot_derivations
        click SlotDerivation href "../../classes/SlotDerivation/"
    

        
      ClassDerivation : sources
        
      ClassDerivation : target_definition
        
          
    
        
        
        ClassDerivation --> "0..1" Any : target_definition
        click Any href "../../classes/Any/"
    

        
      ClassDerivation : value_mappings
        
          
    
        
        
        ClassDerivation --> "*" KeyVal : value_mappings
        click KeyVal href "../../classes/KeyVal/"
    

        
      
```





## Inheritance
* [SpecificationComponent](../classes/SpecificationComponent.md)
    * [ElementDerivation](../classes/ElementDerivation.md)
        * **ClassDerivation**


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [populated_from](../slots/populated_from.md) | 0..1 <br/> [ClassReference](../types/ClassReference.md) | Source class to derive this target class from | direct |
| [sources](../slots/sources.md) | * <br/> [ClassReference](../types/ClassReference.md) | Deprecated | direct |
| [joins](../slots/joins.md) | * <br/> [AliasedClass](../classes/AliasedClass.md) | Additional classes to be joined to derive instances of the target class | direct |
| [slot_derivations](../slots/slot_derivations.md) | * <br/> [SlotDerivation](../classes/SlotDerivation.md) | Instructions on how to derive the slots of this target class from source data | direct |
| [target_definition](../slots/target_definition.md) | 0..1 <br/> [Any](../classes/Any.md) | LinkML class definition object for this slot | direct |
| [pivot_operation](../slots/pivot_operation.md) | 0..1 <br/> [PivotOperation](../classes/PivotOperation.md) | Configuration for pivot (unmelt) operations at class level | direct |
| [mint_ids](../slots/mint_ids.md) | 0..1 <br/> [Boolean](../types/Boolean.md) | Overrides the specification's mint_ids, and the target class's entry in class... | direct |
| [name](../slots/name.md) | 1 <br/> [String](../types/String.md) | Name of the element in the target schema | [ElementDerivation](../classes/ElementDerivation.md) |
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
| [TransformationSpecification](../classes/TransformationSpecification.md) | [class_derivations](../slots/class_derivations.md) | range | [ClassDerivation](../classes/ClassDerivation.md) |
| [ObjectDerivation](../classes/ObjectDerivation.md) | [class_derivations](../slots/class_derivations.md) | range | [ClassDerivation](../classes/ClassDerivation.md) |
| [SlotDerivation](../classes/SlotDerivation.md) | [class_derivations](../slots/class_derivations.md) | range | [ClassDerivation](../classes/ClassDerivation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:ClassDerivation |
| native | linkmlmap:ClassDerivation |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: ClassDerivation
description: A specification of how to derive a target class from a source class.
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  populated_from:
    name: populated_from
    description: Source class to derive this target class from.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: ClassReference
  sources:
    name: sources
    description: Deprecated. Use populated_from instead.
    deprecated: Deprecated. Use populated_from instead. See https://github.com/linkml/linkml-map/issues/193
      for planned list support in populated_from. Will be removed in a future version.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: ClassReference
    multivalued: true
  joins:
    name: joins
    description: Additional classes to be joined to derive instances of the target
      class
    comments:
    - supports cross-table lookups via source_key/lookup_key or the join_on field
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ClassDerivation
    range: AliasedClass
    multivalued: true
    inlined: true
  slot_derivations:
    name: slot_derivations
    description: Instructions on how to derive the slots of this target class from
      source data.
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - TransformationSpecification
    - ClassDerivation
    range: SlotDerivation
    multivalued: true
    inlined: true
  target_definition:
    name: target_definition
    description: LinkML class definition object for this slot.
    comments:
    - currently defined as Any to avoid coupling with metamodel
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ClassDerivation
    - SlotDerivation
    range: Any
  pivot_operation:
    name: pivot_operation
    description: Configuration for pivot (unmelt) operations at class level
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - ClassDerivation
    - SlotDerivation
    range: PivotOperation
  mint_ids:
    name: mint_ids
    description: Overrides the specification's mint_ids, and the target class's entry
      in class_defaults, for this class derivation. Set to false on classes whose
      identifiers other records reference, so a missing derivation is an error rather
      than a content hash.
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - TransformationSpecification
    - ClassDefault
    - ClassDerivation
    range: boolean

```
</details>

### Induced

<details>
```yaml
name: ClassDerivation
description: A specification of how to derive a target class from a source class.
from_schema: https://w3id.org/linkml/transformer
is_a: ElementDerivation
attributes:
  populated_from:
    name: populated_from
    description: Source class to derive this target class from.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ClassDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: ClassReference
  sources:
    name: sources
    description: Deprecated. Use populated_from instead.
    deprecated: Deprecated. Use populated_from instead. See https://github.com/linkml/linkml-map/issues/193
      for planned list support in populated_from. Will be removed in a future version.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ClassDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    range: ClassReference
    multivalued: true
  joins:
    name: joins
    description: Additional classes to be joined to derive instances of the target
      class
    comments:
    - supports cross-table lookups via source_key/lookup_key or the join_on field
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ClassDerivation
    domain_of:
    - ClassDerivation
    range: AliasedClass
    multivalued: true
    inlined: true
  slot_derivations:
    name: slot_derivations
    description: Instructions on how to derive the slots of this target class from
      source data.
    from_schema: https://w3id.org/linkml/transformer
    owner: ClassDerivation
    domain_of:
    - TransformationSpecification
    - ClassDerivation
    range: SlotDerivation
    multivalued: true
    inlined: true
  target_definition:
    name: target_definition
    description: LinkML class definition object for this slot.
    comments:
    - currently defined as Any to avoid coupling with metamodel
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ClassDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    range: Any
  pivot_operation:
    name: pivot_operation
    description: Configuration for pivot (unmelt) operations at class level
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ClassDerivation
    domain_of:
    - ClassDerivation
    - SlotDerivation
    range: PivotOperation
  mint_ids:
    name: mint_ids
    description: Overrides the specification's mint_ids, and the target class's entry
      in class_defaults, for this class derivation. Set to false on classes whose
      identifiers other records reference, so a missing derivation is an error rather
      than a content hash.
    from_schema: https://w3id.org/linkml/transformer
    owner: ClassDerivation
    domain_of:
    - TransformationSpecification
    - ClassDefault
    - ClassDerivation
    range: boolean
  name:
    name: name
    description: Name of the element in the target schema
    from_schema: https://w3id.org/linkml/transformer
    identifier: true
    owner: ClassDerivation
    domain_of:
    - SchemaReference
    - ElementDerivation
    - ClassDefault
    - ObjectDerivation
    - SlotDerivation
    - EnumDerivation
    - PermissibleValueDerivation
    - Agent
    range: string
    required: true
  copy_directives:
    name: copy_directives
    description: Directives controlling which sub-elements of the source element are
      copied into the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    owner: ClassDerivation
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
    owner: ClassDerivation
    domain_of:
    - ElementDerivation
    range: Any
  is_a:
    name: is_a
    description: The parent element that the derived target element inherits from.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:is_a
    owner: ClassDerivation
    domain_of:
    - ElementDerivation
    range: ElementDerivation
  mixins:
    name: mixins
    description: Mixin elements applied to the derived target element.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: linkml:mixins
    owner: ClassDerivation
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
    owner: ClassDerivation
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
    owner: ClassDerivation
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
    owner: ClassDerivation
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
    owner: ClassDerivation
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
    owner: ClassDerivation
    domain_of:
    - ElementDerivation
    range: boolean
  description:
    name: description
    description: description of the specification component
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    slot_uri: dcterms:description
    owner: ClassDerivation
    domain_of:
    - SpecificationComponent
    range: string
  implements:
    name: implements
    description: A reference to a specification that this component implements.
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: ClassDerivation
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
    owner: ClassDerivation
    domain_of:
    - SpecificationComponent
    range: string
    multivalued: true

```
</details></div>