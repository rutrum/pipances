## Context

The financial pipeline app is greenfield — no code exists yet. The tech stack has been decided (see AGENTS.md): Python 3.12+, FastAPI, Polars, SQLAlchemy async, Tailwind+DaisyUI, HTMX. The project needs a working skeleton before any features can be built.

The user uses Nix for system-level tooling and uv for Python dependency management. Both must work together seamlessly.

## Goals / Non-Goals

**Goals:**
- `pyproject.toml` declares all Python dependencies and project metadata (scaffolded by `uv init`, deps added via `uv add`)
- `src/financial_pipeline/` package layout with `__init__.py`
- `flake.nix` provides a dev shell with uv and tailwindcss standalone CLI (uv manages Python, not Nix)
- `uv sync` resolves and installs all dependencies successfully
- `nix develop` drops into a shell with uv and tailwindcss available

**Non-Goals:**
- No application code (routes, models, templates) — that's subsequent changes
- No CI/CD configuration
- No Docker/container setup
- No Tailwind build pipeline yet (just the CLI available in the shell)

## Decisions

### src layout over flat layout
Use `src/financial_pipeline/` rather than a top-level `financial_pipeline/` package. The src layout prevents accidental imports of the uninstalled package and is the modern Python convention. uv and setuptools both handle it well.

### uv as the Python package manager
uv is already chosen per AGENTS.md. The `pyproject.toml` will use standard PEP 621 metadata. uv generates a lockfile (`uv.lock`) for reproducibility.

### Nix flake wrapping uv
The flake provides a `devShells.default` that makes uv and tailwindcss available. Python itself is managed by uv (not Nix) — uv downloads and manages the Python interpreter. The flake only provides non-Python system tools.

### Tailwind standalone CLI via Nix
Use the `tailwindcss` standalone binary (no Node.js) provided through Nix packages. This avoids a Node.js dependency entirely.

## Risks / Trade-offs

- [Tailwind standalone CLI may lag behind npm version] → Acceptable for this project; DaisyUI compatibility should be verified when the build pipeline is set up in a later change.
- [uv.lock is not yet a stable format] → uv is mature enough for production use; lock format changes are rare and handled by `uv sync`.
