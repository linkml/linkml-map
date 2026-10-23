---
search:
  boost: 10.0
---

# Class: Agent 


_An entity that can create or contribute to a digital object, such as an author or creator._



<div data-search-exclude markdown="1">


* __NOTE__: this is an abstract class and should not be instantiated directly


URI: [linkmlmap:class/Agent](https://w3id.org/linkml/transformer/class/Agent)





```mermaid
 classDiagram
    class Agent
    click Agent href "../../classes/Agent/"
      Agent <|-- Person
        click Person href "../../classes/Person/"
      Agent <|-- Organization
        click Organization href "../../classes/Organization/"
      Agent <|-- Software
        click Software href "../../classes/Software/"
      
      Agent : id
        
      Agent : name
        
      Agent : type
        
      
```





## Inheritance
* **Agent**
    * [Person](../classes/Person.md)
    * [Organization](../classes/Organization.md)
    * [Software](../classes/Software.md)


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [id](../slots/id.md) | 1 <br/> [Uriorcurie](../types/Uriorcurie.md) | Identifier for the agent | direct |
| [name](../slots/name.md) | 0..1 <br/> [String](../types/String.md) | Name of the agent | direct |
| [type](../slots/type.md) | 0..1 <br/> [String](../types/String.md) | Type of the agent | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [TransformationSpecification](../classes/TransformationSpecification.md) | [creator](../slots/creator.md) | range | [Agent](../classes/Agent.md) |
| [TransformationSpecification](../classes/TransformationSpecification.md) | [author](../slots/author.md) | range | [Agent](../classes/Agent.md) |
| [TransformationSpecification](../classes/TransformationSpecification.md) | [reviewer](../slots/reviewer.md) | range | [Agent](../classes/Agent.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:Agent |
| native | linkmlmap:Agent |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: Agent
description: An entity that can create or contribute to a digital object, such as
  an author or creator.
from_schema: https://w3id.org/linkml/transformer
abstract: true
attributes:
  id:
    name: id
    description: Identifier for the agent
    from_schema: https://w3id.org/linkml/transformer
    identifier: true
    domain_of:
    - TransformationSpecification
    - Agent
    range: uriorcurie
  name:
    name: name
    description: Name of the agent
    from_schema: https://w3id.org/linkml/transformer
    slot_uri: schema:name
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
  type:
    name: type
    description: Type of the agent
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    designates_type: true
    domain_of:
    - Agent
    range: string

```
</details>

### Induced

<details>
```yaml
name: Agent
description: An entity that can create or contribute to a digital object, such as
  an author or creator.
from_schema: https://w3id.org/linkml/transformer
abstract: true
attributes:
  id:
    name: id
    description: Identifier for the agent
    from_schema: https://w3id.org/linkml/transformer
    identifier: true
    owner: Agent
    domain_of:
    - TransformationSpecification
    - Agent
    range: uriorcurie
    required: true
  name:
    name: name
    description: Name of the agent
    from_schema: https://w3id.org/linkml/transformer
    slot_uri: schema:name
    owner: Agent
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
  type:
    name: type
    description: Type of the agent
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    designates_type: true
    owner: Agent
    domain_of:
    - Agent
    range: string

```
</details></div>