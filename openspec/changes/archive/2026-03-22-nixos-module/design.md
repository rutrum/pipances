# Design: NixOS Module + Env Var Rename

## Env Var Rename

| Old | New |
|-----|-----|
| `FINANCIAL_PIPELINE_STATIC_DIR` | `PIPANCES_STATIC_DIR` |
| `FINANCIAL_PIPELINE_DB_PATH` | `PIPANCES_DB_PATH` |
| `FINANCIAL_PIPELINE_IMPORTERS_DIR` | `PIPANCES_IMPORTERS_DIR` |
| `FINANCIAL_PIPELINE_HOST` | `PIPANCES_HOST` |
| `FINANCIAL_PIPELINE_PORT` | `PIPANCES_PORT` |

Clean rename, no fallback to old names.

## NixOS Module

### File: `nix/modules/nixos/pipances.nix`

Standard NixOS module signature `{ config, lib, pkgs, ... }` — no blueprint extras, so consumers don't need special wiring.

### Options (`services.pipances.*`)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable` | bool | `false` | Enable the service |
| `package` | package | (required) | The app package — consumer must set this |
| `port` | int | `8098` | Listening port |
| `host` | str | `"0.0.0.0"` | Bind address |
| `dataDir` | str | `"/var/lib/pipances"` | Database directory |
| `importersDir` | nullOr path | `null` | Custom importers directory (replaces built-in) |
| `openFirewall` | bool | `false` | Open the port in the firewall |
| `user` | str | `"pipances"` | Service user |
| `group` | str | `"pipances"` | Service group |

### systemd Service

- `ExecStart` runs the package binary
- Environment variables set from options:
  - `PIPANCES_DB_PATH=${cfg.dataDir}/pipances.db`
  - `PIPANCES_HOST=${cfg.host}`
  - `PIPANCES_PORT=${toString cfg.port}`
  - `PIPANCES_IMPORTERS_DIR` only set when `cfg.importersDir != null`
- `StateDirectory = "pipances"` (auto-creates `/var/lib/pipances`)
- Static user/group creation
- Hardening: `ProtectHome=true`, `NoNewPrivileges=true`, `ProtectSystem=strict`, `PrivateTmp=true`, `ReadWritePaths=[cfg.dataDir]`

### Consumer Pattern

```nix
# Consumer's flake.nix
inputs.pipances.url = "...";

# Consumer's configuration.nix
{ inputs, system, ... }:
{
  imports = [ inputs.pipances.nixosModules.pipances ];
  services.pipances = {
    enable = true;
    package = inputs.pipances.packages.${system}.financial-pipeline;
    importersDir = "/etc/pipances/importers";
  };
}
```

## Nix Package Updates

The `financial-pipeline.nix` wrapper script updates env var names from `FINANCIAL_PIPELINE_*` to `PIPANCES_*`. The `docker.nix` container image does the same.
