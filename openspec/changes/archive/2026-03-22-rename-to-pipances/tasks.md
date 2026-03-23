## 1. Rename Python Package

- [x] 1.1 `git mv src/financial_pipeline src/pipances`
- [x] 1.2 Delete all `__pycache__` directories under `src/`
- [x] 1.3 Find-and-replace `financial_pipeline` with `pipances` in all Python source files (`src/pipances/`)
- [x] 1.4 Find-and-replace `financial_pipeline` with `pipances` in all test files (`tests/`)
- [x] 1.5 Find-and-replace `financial_pipeline` with `pipances` in `scripts/seed.py`

## 2. Update Build Configuration

- [x] 2.1 Update `pyproject.toml`: project name to `pipances`, package directory, entry points
- [x] 2.2 Run `uv lock` to regenerate `uv.lock`
- [x] 2.3 Update `justfile`: replace `financial_pipeline` and `financial-pipeline` references
- [x] 2.4 Update `input.css`: Tailwind content path from `financial_pipeline` to `pipances`

## 3. Update Nix Packaging

- [x] 3.1 `git mv nix/packages/financial-pipeline.nix nix/packages/pipances.nix`
- [x] 3.2 Update references inside `nix/packages/pipances.nix`
- [x] 3.3 Update `nix/packages/docker.nix`: image name and package references
- [x] 3.4 Update `nix/checks/nixos-module.nix`: package references
- [x] 3.5 Update `nix/modules/nixos/pipances.nix`: any remaining `financial-pipeline` references

## 4. Update Templates and Documentation

- [x] 4.1 Update page title / branding in `base.html` and `_navbar.html`
- [x] 4.2 Update `CLAUDE.md` project description
- [x] 4.3 Update `AGENTS.md` references

## 5. Verify

- [x] 5.1 Run `grep -r "financial.pipeline" src/ tests/ scripts/ nix/ justfile input.css pyproject.toml` to check for missed references
- [x] 5.2 Run `just test` to verify all tests pass
- [x] 5.3 Run `just lint` to verify code quality
