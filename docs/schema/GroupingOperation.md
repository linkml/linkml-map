---
search:
  boost: 10.0
---

# Class: GroupingOperation 

<div data-search-exclude markdown="1">



URI: [linkmlmap:GroupingOperation](https://w3id.org/linkml/transformer/GroupingOperation)





```mermaid
 classDiagram
    class GroupingOperation
    click GroupingOperation href "../GroupingOperation/"
      TransformationOperation <|-- GroupingOperation
        click TransformationOperation href "../TransformationOperation/"
      
      GroupingOperation : null_handling
        
          
    
        
        
        GroupingOperation --> "0..1" InvalidValueHandlingStrategy : null_handling
        click InvalidValueHandlingStrategy href "../InvalidValueHandlingStrategy/"
    

        
      
```





## Inheritance
* [TransformationOperation](TransformationOperation.md)
    * **GroupingOperation**


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [null_handling](null_handling.md) | 0..1 <br/> [InvalidValueHandlingStrategy](InvalidValueHandlingStrategy.md) |  | direct |















## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:GroupingOperation |
| native | linkmlmap:GroupingOperation |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: GroupingOperation
from_schema: https://w3id.org/linkml/transformer
is_a: TransformationOperation
attributes:
  null_handling:
    name: null_handling
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - AggregationOperation
    - GroupingOperation
    range: InvalidValueHandlingStrategy

```
</details>

### Induced

<details>
```yaml
name: GroupingOperation
from_schema: https://w3id.org/linkml/transformer
is_a: TransformationOperation
attributes:
  null_handling:
    name: null_handling
    from_schema: https://w3id.org/linkml/transformer
    owner: GroupingOperation
    domain_of:
    - AggregationOperation
    - GroupingOperation
    range: InvalidValueHandlingStrategy

```
</details></div>