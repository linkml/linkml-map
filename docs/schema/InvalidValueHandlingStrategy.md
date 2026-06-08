---
search:
  boost: 2.0
---


# Enum: InvalidValueHandlingStrategy 



<div data-search-exclude markdown="1">

URI: [linkmlmap:InvalidValueHandlingStrategy](https://w3id.org/linkml/transformer/InvalidValueHandlingStrategy)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| IGNORE | None |  |
| TREAT_AS_ZERO | None |  |
| ERROR_OUT | None |  |




## Slots

| Name | Description |
| ---  | --- |
| [null_handling](null_handling.md) | How to handle null values encountered during aggregation |
| [invalid_value_handling](invalid_value_handling.md) | How to handle values that cannot be interpreted as valid input to the aggrega... |










## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/linkml/transformer






## LinkML Source

<details>
```yaml
name: InvalidValueHandlingStrategy
from_schema: https://w3id.org/linkml/transformer
rank: 1000
permissible_values:
  IGNORE:
    text: IGNORE
  TREAT_AS_ZERO:
    text: TREAT_AS_ZERO
  ERROR_OUT:
    text: ERROR_OUT

```
</details>

</div>