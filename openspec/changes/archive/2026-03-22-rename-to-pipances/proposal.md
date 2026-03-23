## Why

The project is currently named "financial-pipeline" which is generic and doesn't work well as a product name. Renaming to "pipances" gives it a distinctive identity — a portmanteau of "pipe" and "finances" that reflects the data pipeline nature of the app while being short and memorable.

## What Changes

- **BREAKING**: Rename Python package from `financial_pipeline` to `pipances` (directory and all imports)
- Rename Nix package from `financial-pipeline` to `pipances`
- Update `pyproject.toml` project name and package configuration
- Update all import statements across source, tests, and scripts
- Update build configuration (`justfile`, `input.css`, Nix files)
- Update project documentation (`CLAUDE.md`, `AGENTS.md`)
- Update UI title/branding in templates
- Leave openspec archive files unchanged (historical records)

## Capabilities

### New Capabilities

None — this is a rename, not a feature change.

### Modified Capabilities

None — no spec-level behavior changes, only internal naming.

## Impact

- **Python package**: `src/financial_pipeline/` directory renamed to `src/pipances/`, all internal imports updated
- **Nix packaging**: Package name, docker image name, and NixOS module references updated
- **Build system**: `justfile`, `input.css` content paths updated
- **Tests**: All test file imports updated
- **Scripts**: `scripts/seed.py` imports updated
- **Dependencies**: `uv.lock` will regenerate after `pyproject.toml` change
- **Deployment**: Anyone using the Nix flake or NixOS module will need to update references
