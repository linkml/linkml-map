---
search:
  boost: 10.0
---

# Class: Agent 


_An entity that can create or contribute to a digital object, such as an author or creator._



<div data-search-exclude markdown="1">


* __NOTE__: this is an abstract class and should not be instantiated directly


URI: [linkmlmap:Agent](https://w3id.org/linkml/transformer/Agent)





```mermaid
 classDiagram
    class Agent
    click Agent href "../Agent/"
      Agent <|-- Person
        click Person href "../Person/"
      Agent <|-- Organization
        click Organization href "../Organization/"
      Agent <|-- Software
        click Software href "../Software/"
      
      Agent : id
        
      Agent : name
        
      Agent : type
        
      
```





## Inheritance
* **Agent**
    * [Person](Person.md)
    * [Organization](Organization.md)
    * [Software](Software.md)


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [id](id.md) | 1 <br/> [Uriorcurie](Uriorcurie.md) | Identifier for the agent | direct |
| [name](name.md) | 0..1 <br/> [String](String.md) | Name of the agent | direct |
| [type](type.md) | 0..1 <br/> [String](String.md) | Type of the agent | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [TransformationSpecification](TransformationSpecification.md) | [creator](creator.md) | range | [Agent](Agent.md) |
| [TransformationSpecification](TransformationSpecification.md) | [author](author.md) | range | [Agent](Agent.md) |
| [TransformationSpecification](TransformationSpecification.md) | [reviewer](reviewer.md) | range | [Agent](Agent.md) |












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