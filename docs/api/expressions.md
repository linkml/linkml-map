# Expression Language

LinkML Map uses a safe subset of Python for expressions in slot derivations.
Expressions are evaluated using [simpleeval](https://github.com/danthedeckie/simpleeval),
which provides sandboxed evaluation of Python-like expressions.

## Basic Usage

Use `expr` in a slot derivation to compute a value from source data:

```yaml
class_derivations:
  Individual:
    populated_from: Person
    slot_derivations:
      full_name:
        expr: "{given_name} + ' ' + {family_name}"
      is_adult:
        expr: "age >= 18"
      label:
        expr: "str(id) + ': ' + name"
```

## Null Propagation with `{variable}`

Wrapping a variable in curly braces `{x}` enables null propagation: if the variable
is `None`, the entire expression returns `None` instead of raising an error.

```yaml
slot_derivations:
  full_name:
    expr: "{given_name} + ' ' + {family_name}"
```

| given_name | family_name | Result |
|---|---|---|
| `"Jane"` | `"Doe"` | `"Jane Doe"` |
| `None` | `"Doe"` | `None` |
| `None` | `None` | `None` |

Bare variables (without braces) do **not** trigger null propagation, which is useful
for conditional expressions:

```yaml
slot_derivations:
  status:
    expr: "'active' if start_date else 'pending'"
```

## Available Functions

### Type Conversion

These functions distribute over lists — applying them to a list applies
them to each element.

| Function | Description | Example |
|---|---|---|
| `str(x)` | Convert to string | `str(42)` → `"42"` |
| `int(x)` | Convert to integer | `int("42")` → `42` |
| `float(x)` | Convert to float | `float("3.14")` → `3.14` |
| `bool(x)` | Convert to boolean | `bool(1)` → `True` |

### Math and String

| Function | Description | Example |
|---|---|---|
| `abs(x)` | Absolute value | `abs(-5)` → `5` |
| `round(x)` | Round to nearest integer | `round(3.7)` → `4` |
| `strlen(x)` | String length | `strlen("hello")` → `5` |

### Aggregation

These operate on lists as a whole (they do not distribute):

| Function | Description | Example |
|---|---|---|
| `max(items)` | Maximum value | `max([1, 3, 2])` → `3` |
| `min(items)` | Minimum value | `min([1, 3, 2])` → `1` |
| `len(items)` | Number of items | `len([1, 2, 3])` → `3` |

### Conditional

```yaml
slot_derivations:
  category:
    expr: "case((age < 18, 'minor'), (age < 65, 'adult'), (True, 'senior'))"
```

The `case()` function takes pairs of `(condition, value)` and returns the value
for the first true condition.

### ID Generation

```yaml
slot_derivations:
  uuid_id:
    expr: 'uuid5("https://example.org/Person", {id})'
```

`uuid5(namespace, name)` generates a deterministic UUID v5 (RFC 4122). The same
namespace and name always produce the same UUID, making it suitable for generating
stable identifiers during transformation. The `name` argument must be a string —
use `str()` to convert if needed (e.g. `uuid5("https://example.org/Person", str({id}))`).

## Collection Distribution

When accessing attributes on a collection, the access distributes over each element:

```yaml
slot_derivations:
  all_person_names:
    expr: "persons.name"          # Returns list of names
  name_lengths:
    expr: "strlen(persons.name)"  # Returns list of string lengths
```

## Numeric Coercion

When comparing values from tabular sources (TSV/CSV), string values that look
like numbers are automatically coerced for comparison operators. This means
expressions like `age > 18` work correctly even when `age` arrives as the
string `"25"` from a TSV file.

## Unrestricted Eval Mode

By default, expressions are evaluated in a sandboxed environment that supports
single-expression Python. For complex multi-statement logic (list comprehensions
with filters, if/else blocks, variable assignment), you can enable
`unrestricted_eval` mode:

```python
transformer = ObjectTransformer(unrestricted_eval=True)
```

This falls back to [asteval](https://newville.github.io/asteval/) for expressions
that exceed simpleeval's capabilities. In unrestricted mode, complex expressions
use a `target = ...` convention to set the result, and `src` to access the full
source object:

```yaml
slot_derivations:
  driving_test_date:
    expr: |
      d_test = [x.important_event_date for x in src.has_important_life_events
                if str(x.event_name) == "PASSED_DRIVING_TEST"]
      if len(d_test):
          target = d_test[0]
```

!!! warning "Security"
    Unrestricted eval allows arbitrary Python execution within asteval's sandbox.
    Only use this with trusted transformation specifications. It can be enabled
    programmatically (e.g. `ObjectTransformer(unrestricted_eval=True)`) or via
    the `--unrestricted-eval` / `--no-unrestricted-eval` flags on `linkml-map map-data`.

## Operators

Standard Python operators are supported:

- Arithmetic: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Boolean: `and`, `or`, `not`
- Containment: `in`, `not in`
- String concatenation: `+`
- Ternary: `x if condition else y`
