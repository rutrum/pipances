# Proposal: NixOS Module + Env Var Rename

## Problem
There's no NixOS module for deploying the app. Users who run NixOS have to manually wire up a systemd service. Additionally, the env vars still use the old `FINANCIAL_PIPELINE_*` prefix instead of the decided `PIPANCES_*` name.

## Solution
1. Rename all `FINANCIAL_PIPELINE_*` env vars to `PIPANCES_*` across Python and Nix code
2. Add a NixOS module at `nix/modules/nixos/pipances.nix` (blueprint auto-exposes as `nixosModules.pipances`)
3. Update the Nix package wrapper to use the new env var names

## Scope
- Rename env vars in: `main.py`, `db.py`, `ingest.py`, `financial-pipeline.nix`, `docker.nix`
- New file: `nix/modules/nixos/pipances.nix`
- No Python package rename (deferred to TODO)
- No auth options (deferred to TODO)
- No spec artifacts needed (infrastructure-only change)
