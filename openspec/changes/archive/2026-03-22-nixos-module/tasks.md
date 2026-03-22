# Tasks: NixOS Module + Env Var Rename

## 1. Rename env vars in Python

- [x] 1.1 `src/financial_pipeline/main.py`: `FINANCIAL_PIPELINE_STATIC_DIR` -> `PIPANCES_STATIC_DIR`
- [x] 1.2 `src/financial_pipeline/db.py`: `FINANCIAL_PIPELINE_DB_PATH` -> `PIPANCES_DB_PATH`
- [x] 1.3 `src/financial_pipeline/ingest.py`: `FINANCIAL_PIPELINE_IMPORTERS_DIR` -> `PIPANCES_IMPORTERS_DIR`

## 2. Rename env vars in Nix packages

- [x] 2.1 `nix/packages/financial-pipeline.nix`: rename all `FINANCIAL_PIPELINE_*` to `PIPANCES_*`
- [x] 2.2 `nix/packages/docker.nix`: rename `FINANCIAL_PIPELINE_DB_PATH` to `PIPANCES_DB_PATH`

## 3. Create NixOS module

- [x] 3.1 Create `nix/modules/nixos/pipances.nix` with options and systemd service config
- [x] 3.2 `git add` the new file (blueprint ignores untracked files)

## 4. Nix eval check

- [x] 4.1 Create `nix/checks/nixos-module.nix` — evaluates module with minimal NixOS config
- [x] 4.2 `nix build .#checks.x86_64-linux.nixos-module` passes

## 5. Verify

- [x] 5.1 `nix flake show` confirms `nixosModules.pipances` and `checks.*.nixos-module` appear
- [x] 5.2 `just test` passes (56/56)
- [x] 5.3 `just fmt` for formatting
