# Functions

## Expression Functions

The following functions are available in `expr` fields within slot derivations.
See the [Expression Language](expressions.md) guide for full details on syntax
and null propagation.

| Function | Description |
|---|---|
| `str(x)` | Convert to string (distributes over lists) |
| `int(x)` | Convert to integer (distributes over lists) |
| `float(x)` | Convert to float (distributes over lists) |
| `bool(x)` | Convert to boolean (distributes over lists) |
| `abs(x)` | Absolute value (distributes over lists) |
| `round(x)` | Round number (distributes over lists) |
| `strlen(x)` | String length (distributes over lists) |
| `max(items)` | Maximum of a list |
| `min(items)` | Minimum of a list |
| `len(items)` | Length of a list |
| `case(pairs...)` | Conditional — first matching `(condition, value)` pair |
| `uuid5(namespace, name)` | Deterministic UUID v5 generation |

## Unit Conversion

::: linkml_map.functions.unit_conversion
