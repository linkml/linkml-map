# CLAUDE.md

## Project Overview

linkml-map is a library for transforming data between different LinkML schemas using declarative transformation specifications.

## Development

- Use `pytest` to run tests
- Use `ruff check` for linting

## Code Patterns

When modifying `ObjectTransformer.map_object`, check for `# EXTRACT:` markers.
If touching a marked section, extract it to a private method first and add a test
in `tests/test_transformer/test_object_transformer_new.py` using `@add_to_test_setup`.
See issue #104 for context.

## Testing

**Always add tests when implementing new features or fixing bugs.** Don't wait to be asked.
For transformation features, use the scaffold-based testing pattern described in `tests/README.md`.
