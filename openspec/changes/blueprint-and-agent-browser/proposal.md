## Why

The current `flake.nix` uses a hand-rolled `forAllSystems` pattern with inline devShell definition. Migrating to numtide/blueprint eliminates this boilerplate and establishes a conventional folder structure (`nix/`) for Nix files in a Python-primary project. Additionally, the Chrome DevTools MCP server is unreliable, so we need `agent-browser` — a Rust-based headless browser CLI for AI agents — available in the devshell as an alternative for browser automation.

## What Changes

- Migrate `flake.nix` to use numtide/blueprint with `prefix = "nix/"` — the flake becomes a minimal input declaration
- Extract the devShell definition into `nix/devshell.nix` using blueprint's argument convention (`{ pkgs, inputs, ... }:`)
- Add a new Nix package `agent-browser` that fetches the prebuilt binary from GitHub releases, patches it for NixOS (via `autoPatchelfHook`), and installs it to `$out/bin`
- Add `agent-browser` to the devshell packages
- Version is a variable at the top of the package file for easy bumping
- Multi-platform support via `stdenv.hostPlatform` (linux-x64, linux-arm64, darwin-x64, darwin-arm64)

## Capabilities

### New Capabilities

None — this is infrastructure/tooling, not user-facing.

### Modified Capabilities

None.

## Impact

- `flake.nix` — rewritten to minimal blueprint declaration
- `nix/devshell.nix` — new file, extracted from current flake
- `nix/packages/agent-browser.nix` — new file, prebuilt binary package
- No application code changes
- Users must run `agent-browser install` once after entering devshell to fetch Chrome for Testing
