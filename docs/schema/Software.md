---
search:
  boost: 10.0
---

# Class: Software 


_A software tool or system used in creating mappings_



<div data-search-exclude markdown="1">



URI: [linkmlmap:Software](https://w3id.org/linkml/transformer/Software)





```mermaid
 classDiagram
    class Software
    click Software href "../Software/"
      Agent <|-- Software
        click Agent href "../Agent/"
      
      Software : id
        
      Software : name
        
      Software : repository_url
        
      Software : type
        
      Software : version
        
      
```





## Inheritance
* [Agent](Agent.md)
    * **Software**


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [version](version.md) | 0..1 <br/> [String](String.md) | Version of the software | direct |
| [repository_url](repository_url.md) | 0..1 <br/> [Uri](Uri.md) | URL to a code repository | direct |
| [id](id.md) | 1 <br/> [Uriorcurie](Uriorcurie.md) | Identifier for the agent | [Agent](Agent.md) |
| [name](name.md) | 0..1 <br/> [String](String.md) | Name of the agent | [Agent](Agent.md) |
| [type](type.md) | 0..1 <br/> [String](String.md) | Type of the agent | [Agent](Agent.md) |















## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:Software |
| native | linkmlmap:Software |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: Software
description: A software tool or system used in creating mappings
from_schema: https://w3id.org/linkml/transformer
is_a: Agent
attributes:
  version:
    name: version
    description: Version of the software
    from_schema: https://w3id.org/linkml/transformer
    domain_of:
    - TransformationSpecification
    - SchemaReference
    - Software
    range: string
  repository_url:
    name: repository_url
    description: URL to a code repository
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    domain_of:
    - Software
    range: uri

```
</details>

### Induced

<details>
```yaml
name: Software
description: A software tool or system used in creating mappings
from_schema: https://w3id.org/linkml/transformer
is_a: Agent
attributes:
  version:
    name: version
    description: Version of the software
    from_schema: https://w3id.org/linkml/transformer
    owner: Software
    domain_of:
    - TransformationSpecification
    - SchemaReference
    - Software
    range: string
  repository_url:
    name: repository_url
    description: URL to a code repository
    from_schema: https://w3id.org/linkml/transformer
    rank: 1000
    owner: Software
    domain_of:
    - Software
    range: uri
  id:
    name: id
    description: Identifier for the agent
    from_schema: https://w3id.org/linkml/transformer
    identifier: true
    owner: Software
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
    owner: Software
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
    owner: Software
    domain_of:
    - Agent
    range: string

```
</details></div>