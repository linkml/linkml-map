---
search:
  boost: 5.0
---

# Slot: type 


_Type of the agent_



<div data-search-exclude markdown="1">



URI: [linkmlmap:type](https://w3id.org/linkml/transformer/type)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Agent](Agent.md) | An entity that can create or contribute to a digital object, such as an autho... |  no  |
| [Person](Person.md) | An individual person who contributes to a mapping specification |  no  |
| [Organization](Organization.md) | An organization or institution that contributes to a mapping specification |  no  |
| [Software](Software.md) | A software tool or system used in creating mappings |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [Agent](Agent.md) |

### Cardinality and Requirements

| Property | Value |
| --- | --- |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Designates Type | Yes |
| Owner | [Agent](Agent.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | linkmlmap:type |
| native | linkmlmap:type |




## LinkML Source

<details>
```yaml
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