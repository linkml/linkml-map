# Contributing

### Testing

See `tests/README.md` for guidance on the scaffold-based testing pattern used in this project.

### Code Style

This project uses [`ruff`](https://docs.astral.sh/ruff/) to lint and format.
Run `uv run ruff check .` and `uv run ruff format .` before opening a pull
request, or install the hooks with `uv run pre-commit install` and let them run
automatically.

Each of these checks are run on each commit using GitHub Actions as a continuous
integration service. Passing all of them is required for accepting a
contribution. If you're unsure how to address the feedback from one of these
tools, please say so either in the description of your pull request or in a
comment, and we will help you.

These code style contribution guidelines have been adapted from the
[cthoyt/cookiecutter-snekpack](https://github.com/cthoyt/cookiecutter-snekpack/blob/main/%7B%7Bcookiecutter.package_name%7D%7D/.github/CODE_OF_CONDUCT.md)
Python package template.
