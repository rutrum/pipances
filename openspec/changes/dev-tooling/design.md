## Context

The project uses uv for Python dependency management, just for task running, and pyproject.toml as the central config file. There is no Node.js — Tailwind runs via standalone CLI and DaisyUI is loaded as a CSS file via Nix flake input.

## Goals / Non-Goals

**Goals:**
- Consistent Python formatting and linting via Ruff
- Consistent Jinja2/HTML formatting and linting via djLint
- Simple `just` recipes to run checks and apply fixes
- All config in `pyproject.toml` (no extra dotfiles)

**Non-Goals:**
- pre-commit hooks (can layer on later)
- Type checking (mypy/pyright — deferred)
- CSS linting (input.css is tiny, output is generated)
- JS linting (only ~18 lines inline in base.html)

## Decisions

### 1. Ruff configuration

**Decision**: Use Ruff for both linting and formatting. Enable a broad but sensible rule set.

**Rules to enable**:
- `E` + `W` (pycodestyle errors/warnings)
- `F` (pyflakes)
- `I` (isort — import sorting)
- `UP` (pyupgrade — modernize syntax)
- `B` (bugbear — common pitfalls)
- `S` (bandit — security checks, selectively)

**Line length**: 88 (Ruff/Black default).

**Target Python version**: `py312` (matches pyproject.toml `requires-python`).

### 2. djLint configuration

**Decision**: Use djLint with `jinja` profile. Start with default rules and tune if needed.

**Key settings**:
- `profile = "jinja"` — understands `{% %}` / `{{ }}` blocks
- `indent = 2` — standard HTML indentation
- `max_line_length = 120` — HTML lines tend to be longer than Python, especially with `hx-*` attributes
- `ignore` — we'll add specific rule ignores as we discover false positives during initial run

### 3. Just recipes

**Decision**: Add these recipes to the justfile:

| Recipe | Command | Purpose |
|--------|---------|---------|
| `just lint` | Run ruff check + djlint lint | Check for issues (no changes) |
| `just fmt` | Run ruff format + djlint reformat | Auto-fix formatting |
| `just check` | Run ruff check + ruff format --check + djlint | Full CI-style check (exit non-zero on issues) |

### 4. Dev dependencies via uv

**Decision**: Add ruff and djlint as uv dev dependencies (`uv add --dev ruff djlint`). This keeps them out of production deps but available in the venv.

## Risks / Trade-offs

- **Initial formatting churn**: First run of `ruff format` and `djlint --reformat` will touch many files. This is a one-time cost — do it in a single commit so blame history stays clean.
- **djLint false positives on HTMX attributes**: djLint may flag `hx-*` attributes as unknown. These can be ignored via config. We'll tune after the first run.
- **Ruff bandit (S) rules may be noisy**: Some security rules flag things that are fine in a single-user self-hosted app (e.g., hardcoded secrets in dev config). We'll selectively ignore these.
