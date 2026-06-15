---
search:
  boost: 2.0
---


# Enum: AggregationType 



<div data-search-exclude markdown="1">

URI: [linkmlmap:AggregationType](https://w3id.org/linkml/transformer/AggregationType)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| SUM | None |  |
| AVERAGE | None |  |
| COUNT | None |  |
| MIN | None |  |
| MAX | None |  |
| STD_DEV | None |  |
| VARIANCE | None |  |
| MEDIAN | None |  |
| MODE | None |  |
| CUSTOM | None |  |
| SET | None |  |
| LIST | None |  |
| ARRAY | None |  |




## Slots

| Name | Description |
| ---  | --- |
| [operator](operator.md) | The aggregation function to apply (for example SUM, AVERAGE, COUNT) |










## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer






## LinkML Source

<details>
```yaml
name: AggregationType
from_schema: https://w3id.org/linkml/transformer
rank: 1000
permissible_values:
  SUM:
    text: SUM
  AVERAGE:
    text: AVERAGE
    aliases:
    - mean
    - avg
    exact_mappings:
    - STATO:0000230
  COUNT:
    text: COUNT
    exact_mappings:
    - STATO:0000047
  MIN:
    text: MIN
  MAX:
    text: MAX
  STD_DEV:
    text: STD_DEV
    exact_mappings:
    - STATO:0000237
  VARIANCE:
    text: VARIANCE
  MEDIAN:
    text: MEDIAN
    exact_mappings:
    - STATO:0000674
  MODE:
    text: MODE
    exact_mappings:
    - STATO:0000033
  CUSTOM:
    text: CUSTOM
  SET:
    text: SET
  LIST:
    text: LIST
  ARRAY:
    text: ARRAY

```
</details>

</div>