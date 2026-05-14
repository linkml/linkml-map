---
search:
  boost: 2.0
---


# Enum: PivotDirectionType 



<div data-search-exclude markdown="1">

URI: [linkmlmap:PivotDirectionType](https://w3id.org/linkml/transformer/PivotDirectionType)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| MELT | None |  |
| UNMELT | None |  |




## Slots

| Name | Description |
| ---  | --- |
| [direction](direction.md) |  |










## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer






## LinkML Source

<details>
```yaml
name: PivotDirectionType
from_schema: https://w3id.org/linkml/transformer
rank: 1000
permissible_values:
  MELT:
    text: MELT
    aliases:
    - unpivot
    - wide to long
  UNMELT:
    text: UNMELT
    aliases:
    - pivot
    - long to wide

```
</details>

</div>