## Why

The app has no production packaging — it can only run from the source tree via `uv run`. We need a Nix package for deployment and a Docker container image for distribution. uv2nix lets us keep uv as the Python dependency manager while building reproducible Nix packages from the lockfile.

## What Changes

- Add uv2nix, pyproject-nix, and pyproject-build-systems as flake inputs
- Create a Nix package for the app using uv2nix to resolve Python deps from `uv.lock`
- Bundle static assets (JS from flake inputs, built CSS from Tailwind) into the package
- Build a Docker container image via `pkgs.dockerTools.buildLayeredImage`
- Make `static/` and `importers/` paths configurable so the app works both in dev (source tree) and production (Nix store)

## Capabilities

### New Capabilities
(None — infrastructure change, no user-facing capabilities)

### Modified Capabilities
(None)

## Impact

- `flake.nix`: Add uv2nix/pyproject-nix/pyproject-build-systems inputs
- `nix/packages/`: New package derivation for the app, Docker image derivation
- `src/financial_pipeline/main.py`: Make `PROJECT_ROOT` / static dir configurable via env var
- `src/financial_pipeline/ingest.py`: Make `IMPORTERS_DIR` configurable via env var
- `nix/devshell.nix`: May need adjustments to work alongside uv2nix
- `uv.lock`: Must be committed (already is, but becomes load-bearing for Nix builds)
