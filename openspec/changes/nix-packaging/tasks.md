## 1. Configurable Paths

- [ ] 1.1 Add env var overrides for static dir, importers dir, and DB path in `main.py` and `ingest.py` with fallback to current `PROJECT_ROOT` behavior
- [ ] 1.2 Add `FINANCIAL_PIPELINE_DB_PATH` env var support in `db.py` for the SQLite database location

## 2. Flake Inputs

- [ ] 2.1 Add `pyproject-nix`, `uv2nix`, and `pyproject-build-systems` as flake inputs with `follows` for nixpkgs
- [ ] 2.2 Ensure `uv.lock` is committed and up to date

## 3. Nix App Package

- [ ] 3.1 Create `nix/packages/financial-pipeline.nix` that uses uv2nix to build a virtualenv from `uv.lock`
- [ ] 3.2 Create a static assets derivation that copies JS from flake inputs and runs tailwindcss to build CSS
- [ ] 3.3 Create a wrapper script derivation that sets env vars and runs `uvicorn financial_pipeline.main:app`
- [ ] 3.4 Verify `nix build .#financial-pipeline` produces a working package

## 4. Docker Image

- [ ] 4.1 Create `nix/packages/docker.nix` using `dockerTools.buildLayeredImage` with the app package
- [ ] 4.2 Verify `nix build .#docker` produces a loadable image
- [ ] 4.3 Test running the Docker image with a mounted volume for the database

## 5. Polish

- [ ] 5.1 Run `just fmt` and `just lint`
- [ ] 5.2 Verify dev workflow (`nix develop` + `uv run`) still works unchanged
