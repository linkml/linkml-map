# Extension Functions

linkml-map ships a curated set of safe built-in functions for use in
[expressions](expressions.md). When you need a function that isn't built in,
you can register your own — without forking linkml-map or wrapping it in a
custom Python harness — by tagging plain Python functions with
`@safe_function` and pointing the CLI at the file.

## Quick example

A user-supplied `my_helpers.py`:

```python
from linkml_map.utils.extensions import safe_function


@safe_function
def normalize_taxon_id(s: str) -> str | None:
    """Strip the 'NCBI:' prefix and pad to 8 digits."""
    if not s:
        return None
    raw = s.removeprefix("NCBI:").strip()
    return f"NCBI:{int(raw):08d}"
```

Then in a trans-spec:

```yaml
# required_extensions: my_helpers.py  (convention; see below)
class_derivations:
  Organism:
    populated_from: SourceOrganism
    slot_derivations:
      tax_id:
        expr: "normalize_taxon_id(taxon)"
```

And at the command line:

```bash
linkml-map map-data -s schema.yaml -T transform.yaml \
  --functions ./my_helpers.py \
  data.tsv -o out.jsonl
```

The flag is repeatable: pass `--functions` (or the short form `-F`) once per
extension file.

## The `@safe_function` contract

Applying `@safe_function` is a **declaration by the author** that the function
is:

- **Pure** — no I/O, no network calls, no global state mutation
- **Bounded-time** — deterministic and fast; runs once per row in a transform
- **Deterministic** — same inputs produce same outputs

linkml-map **does not verify** these properties. The name "safe" reflects what
*you* are declaring about the function, not what linkml-map enforces. This is
the same posture as `typing.final` or `@SafeVarargs` in other ecosystems.

The trust model is identical to `pip install`: anything in a module you import
will run. If you're importing a third-party extension, treat it like any other
dependency.

## When NOT to use extensions

Extensions are not an escape hatch for putting transformation logic in Python.
They exist for **named atomic operations** that read cleaner as a name than as
an expression chain — `slugify(name)` instead of
`replace(replace(lower(strip(name)), ' ', '_'), ',', '')`.

If the function you're tempted to write is more than a few lines of pure
data manipulation, ask first whether it belongs in the trans-spec or in the
source/target schema. The declarative spec is the documentation of what the
transformation does; pulling logic out into Python hides it from review.

## Override semantics

A `@safe_function` may shadow a built-in if you explicitly say so:

```python
@safe_function(override=True)
def lower(s: str) -> str:
    return s.casefold()  # locale-aware, replaces the built-in str.lower
```

- **Without `override=True`**: collision with a built-in raises `ExtensionError`
  at load time — protects against accidental shadowing from a typo.
- **With `override=True` but no matching built-in**: logged as a warning (still
  loaded) — useful as a typo catcher for the override case.
- **Collision between two extensions**: always an error. Pick one.

There is no CLI flag to enable overrides. The decision lives on the function
declaration, where the author is responsible for it.

## List-style functions

By default, scalar functions distribute over lists and propagate `None`
(`slugify([a, b, None])` → `[slugify(a), slugify(b), None]`). For functions
that legitimately accept a list as their first argument (aggregators, etc.),
opt out:

```python
@safe_function(distributes=False)
def median(items: list[float]) -> float:
    sorted_items = sorted(items)
    return sorted_items[len(sorted_items) // 2]
```

## Required-extension convention

A trans-spec that references an extension function won't run without
`--functions`. The runtime error is clear (`Unknown function 'foo'. (If this
is a custom function, pass it via --functions <path>.)`), but it's still
runtime. Until linkml-map gains a declarative `required_extensions:` key, the
convention is to note the dependency in a header comment on the spec:

```yaml
# required_extensions:
#   - my_helpers.py
#
id: https://example.org/my-transform
class_derivations:
  ...
```

## Programmatic use

Python callers can skip the CLI and set extensions directly on the transformer:

```python
from linkml_map.transformer.object_transformer import ObjectTransformer
from linkml_map.utils.extensions import load_extensions

ext = load_extensions(["./my_helpers.py"])
tr = ObjectTransformer(extension_functions=ext)
```

`extension_functions` accepts any `dict[str, Callable]`, so you can also bypass
the loader entirely and hand-build the dict if you prefer (skipping the
decorator-tagging step).

## API reference

::: linkml_map.utils.extensions
