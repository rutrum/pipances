## 1. Configurable Paths

- [x] 1.1 Add env var overrides for static dir, importers dir, and DB path in `main.py` and `ingest.py` with fallback to current `PROJECT_ROOT` behavior
- [x] 1.2 Add `FINANCIAL_PIPELINE_DB_PATH` env var support in `db.py` for the SQLite database location

## 2. Flake Inputs

- [x] 2.1 Add `pyproject-nix`, `uv2nix`, and `pyproject-build-systems` as flake inputs with `follows` for nixpkgs
- [x] 2.2 Ensure `uv.lock` is committed and up to date

## 3. Nix App Package

- [x] 3.1 Create `nix/packages/financial-pipeline.nix` that uses uv2nix to build a virtualenv from `uv.lock`
- [x] 3.2 Create a static assets derivation that copies JS from flake inputs and runs tailwindcss to build CSS
- [x] 3.3 Create a wrapper script derivation that sets env vars and runs `uvicorn financial_pipeline.main:app`
- [x] 3.4 Verify `nix build .#financial-pipeline` produces a working package

## 4. Docker Image

- [x] 4.1 Create `nix/packages/docker.nix` using `dockerTools.buildLayeredImage` with the app package
- [x] 4.2 Verify `nix build .#docker` produces a loadable image
- [x] 4.3 Load the Docker image, run the container with a seeded database, and verify the app is accessible

## 5. Browser Verification

- [x] 5.1 With the container running, open the dashboard in agent-browser and verify charts render
- [x] 5.2 Navigate to the transactions page and verify data displays
- [x] 5.3 Navigate to the inbox page and verify it loads
- [x] 5.4 Navigate to the settings page and verify it loads

## 6. Polish

- [x] 6.1 Run `just fmt` and `just lint`
- [x] 6.2 Verify dev workflow (`nix develop` + `uv run`) still works unchanged
