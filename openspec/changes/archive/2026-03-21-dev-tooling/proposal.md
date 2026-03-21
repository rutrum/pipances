## Why

The project has ~920 lines of Python and 15 Jinja2 templates with no automated code quality tooling. As the codebase grows, inconsistent formatting and common lint issues will accumulate. Adding linting and formatting now, while the codebase is small, means a clean baseline and minimal churn to fix existing issues.

## What Changes

- Add **Ruff** as a dev dependency for Python linting and formatting (replaces flake8, black, isort, etc.)
- Add **djLint** as a dev dependency for Jinja2/HTML template linting and formatting
- Configure both tools in `pyproject.toml`
- Add `just` recipes for running lint/format commands
- Document the new recipes in `AGENTS.md`

## Capabilities

### New Capabilities

None (infrastructure/tooling only).

### Modified Capabilities

None.

## Impact

- **pyproject.toml**: Add `ruff` and `djlint` as dev dependencies; add `[tool.ruff]` and `[tool.djlint]` configuration sections
- **justfile**: Add `lint`, `fmt`, and `check` recipes
- **AGENTS.md**: Document new recipes
- **Source files**: May be reformatted by initial run of `ruff format` and `djlint --reformat`
