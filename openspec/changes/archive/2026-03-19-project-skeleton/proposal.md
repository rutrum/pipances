## Why

The financial pipeline app has no code yet. Before any features can be built, we need a working project skeleton: Python package structure, dependency management (uv + pyproject.toml), and a Nix flake dev shell. This is the foundation everything else builds on.

## What Changes

- Use `uv init` to scaffold `pyproject.toml`, then add all Python dependencies via `uv add`
- Create `flake.nix` providing a dev shell with uv and tailwindcss CLI (Python is managed by uv, not Nix)
- Set up `src/financial_pipeline/` package layout with `__init__.py`
- Ensure `uv sync` resolves and installs all deps
- Ensure `nix develop` drops into a shell with uv and tailwindcss available

## Capabilities

(none — this is infrastructure, not an application capability)

## Impact

- New files: `pyproject.toml`, `uv.lock`, `flake.nix`, `src/financial_pipeline/__init__.py`
- New tooling dependency: Nix flake with uv and tailwindcss CLI
- No existing code affected (greenfield)
