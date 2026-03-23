## Context

The project is named "financial-pipeline" with Python package `financial_pipeline`. The name appears in:
- Python package directory: `src/financial_pipeline/`
- All Python imports (~50 files reference `financial_pipeline`)
- `pyproject.toml` project metadata
- Nix package definition: `nix/packages/financial-pipeline.nix`
- Docker/container image: `nix/packages/docker.nix`
- NixOS module: `nix/modules/nixos/pipances.nix` (already partially renamed)
- NixOS module check: `nix/checks/nixos-module.nix`
- Build config: `justfile`, `input.css`
- Templates: page titles, navbar branding
- Scripts: `scripts/seed.py`
- Documentation: `CLAUDE.md`, `AGENTS.md`
- OpenSpec archives (~30 files, historical)

## Goals / Non-Goals

**Goals:**
- Rename Python package from `financial_pipeline` to `pipances`
- Rename Nix package from `financial-pipeline` to `pipances`
- Update all imports, references, and build configuration
- Ensure tests pass after rename
- Update UI branding (page titles, navbar)

**Non-Goals:**
- Renaming the git repository or its directory on disk (that's external to the codebase)
- Updating openspec archive files (historical records, no functional impact)
- Changing the `uv.lock` manually (it regenerates from `pyproject.toml`)

## Decisions

**1. Rename strategy: move directory, then find-and-replace**

Rename `src/financial_pipeline/` to `src/pipances/` via `git mv`, then do a project-wide find-and-replace of `financial_pipeline` → `pipances` and `financial-pipeline` → `pipances` in active files.

*Alternative*: Gradual rename with compatibility shims. Rejected — unnecessary complexity for a single-user project with no downstream consumers.

**2. Skip openspec archives**

Archived change files are historical records. Updating them adds churn with no functional benefit. The old name in archives is accurate — that *was* the name when those changes were made.

**3. Nix package file rename**

Rename `nix/packages/financial-pipeline.nix` to `nix/packages/pipances.nix`. Blueprint auto-discovers based on filename, so the flake output name changes automatically.

**4. Regenerate uv.lock**

After updating `pyproject.toml`, run `uv lock` to regenerate the lockfile. Don't try to edit it manually.

## Risks / Trade-offs

- **[Risk] Missed references** → Run tests and `grep -r financial` after rename to catch stragglers
- **[Risk] Nix flake consumers break** → The NixOS module already uses `pipances` as the option namespace; the package output name changes from `financial-pipeline` to `pipances`
- **[Risk] __pycache__ stale files** → Delete `__pycache__` directories after rename to avoid import confusion
