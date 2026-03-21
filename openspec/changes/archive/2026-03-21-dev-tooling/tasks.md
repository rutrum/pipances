## 1. Add Dev Dependencies

- [x] 1.1 Run `uv add --dev ruff djlint` to add both as dev dependencies

## 2. Configure Ruff

- [x] 2.1 Add `[tool.ruff]` section to `pyproject.toml` with target-version, line-length, and selected rules (E, W, F, I, UP, B, S)
- [x] 2.2 Add any necessary `[tool.ruff.lint.per-file-ignores]` (e.g., S rules for config files)

## 3. Configure djLint

- [x] 3.1 Add `[tool.djlint]` section to `pyproject.toml` with profile, indent, and max_line_length
- [x] 3.2 Run djLint once and tune `ignore` list for false positives on HTMX attributes

## 4. Add Just Recipes

- [x] 4.1 Add `lint` recipe (ruff check + djlint lint)
- [x] 4.2 Add `fmt` recipe (ruff format + djlint reformat)
- [x] 4.3 Add `check` recipe (full CI-style check, exits non-zero on issues)

## 5. Apply Initial Formatting

- [x] 5.1 Run `just fmt` to apply initial formatting to all files
- [x] 5.2 Run `just lint` to check for remaining issues and fix or ignore as appropriate

## 6. Documentation

- [x] 6.1 Update `AGENTS.md` build/run section to document new `lint`, `fmt`, and `check` recipes
