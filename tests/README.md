# Testing

## Scaffold-Based Testing Pattern

This project uses a **scaffold-based testing pattern** for transformation tests. The pattern:

1. A **scaffold** provides base schemas, transform spec, input data, and expected output
2. **Setup functions** patch the scaffold incrementally using `apply_schema_patch()` / `apply_transform_patch()`
3. **Unit tests** run each setup function in isolation
4. **Integration tests** run all setups cumulatively, catching interaction bugs

This pattern is preferred for transformation tests because it:
- Makes tests concise (just patches, not full schemas)
- Catches both individual feature bugs and feature interaction bugs
- Builds up a realistic, complex test scenario over time

### Existing Scaffolds

- **Simple** (`tests/scaffold/`): Basic slot derivations, Person→Agent transforms.
  Fixtures: `scaffold`, `integration_scaffold`. Decorator: `@add_to_test_setup`

- **Container** (`tests/scaffold_container/`): FK lookups, flattening, cross-class transforms.
  Fixtures: `container_scaffold`, `integration_container_scaffold`. Decorator: `@add_to_container_test_setup`

### When to Create a New Scaffold

If testing a feature that doesn't fit existing scaffolds (e.g., different schema shape,
inheritance hierarchies, enum-heavy transforms), create a new scaffold directory following
the same pattern. See `tests/scaffold/` for the structure.

### Utilities

See `tests/scaffold/utils/apply_patch.py` for patching utilities.

### When to Use Traditional Tests

It's okay to use traditional tests (not scaffold-based) when:
- Testing utility functions (unit conversion, eval_utils, etc.)
- Testing error handling or edge cases that don't fit the scaffold pattern
- Testing components outside the transformer (CLI, schema mapping, inverter)
- Quick regression tests for specific bugs
