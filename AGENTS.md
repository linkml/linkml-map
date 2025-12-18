# AGENTS.md for linkml-map

LinkML Map is a framework for specifying and executing mappings between data models.

TODO: fill in extra description here

## Repo management

This repo uses `uv` for managing dependencies. Never use commands like `pip` to add or manage dependencies.
`uv run` is the best way to run things, unless you are using `justfile` or `makefile` target

`mkdocs` is used for documentation.
## This is a Python repository

Layout:

 * `src/linkml_map/` - Code goes here
 * `docs` - mkdocs docs
 * `mkdocs.yml` - index of docs
 * `tests/input` - example files

Building and testing:

* `just --list` to see all commands
* `just test` performs unit tests, doctests, ruff/linting
* `just test-full` as above plus integration tests

You can run the underlying commands (with `uv run ...`) but in general justfile targets should be favored.

Best practice:

* Use doctests liberally - these serve as both explanatory examples for humans and as unit tests
* For longer examples, write pytest tests
* always write pytest functional style rather than unittest OO style
* use modern pytest idioms, including `@pytest.mark.parametrize` to test for combinations of inputs
* NEVER write mock tests unless requested. I need to rely on tests to know if something breaks
* For tests that have external dependencies, you can do `@pytest.mark.integration`
* Do not "fix" issues by changing or weakening test conditions. Try harder, or ask questions if a test fails.
* Avoid try/except blocks, these can mask bugs
* Fail fast is a good principle
* Follow the DRY principle
* Avoid repeating chunks of code, but also avoid premature over-abstraction
* Pydantic or LinkML is favored for data objects
* For state in engine-style OO classes, dataclasses is favored
* Declarative principles are favored
* Always use type hints, always document methods and classes
* **Always add tests when implementing new features or fixing bugs.** Don't wait to be asked.
* For transformation tests, use the scaffold-based testing pattern described in `tests/README.md`

## Code Patterns

When modifying `ObjectTransformer.map_object`, check for `# EXTRACT:` markers.
If touching a marked section, extract it to a private method first and add a test
in `tests/test_transformer/test_object_transformer_new.py` using `@add_to_test_setup`.
See issue #104 for context.