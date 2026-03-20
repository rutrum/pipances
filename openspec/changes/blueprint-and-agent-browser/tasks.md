## 1. Blueprint Migration

- [x] 1.1 Create `nix/devshell.nix` — extract current devShell using blueprint argument convention (`{ pkgs, inputs, perSystem, ... }:`)
- [x] 1.2 Rewrite `flake.nix` — minimal blueprint declaration with `prefix = "nix/"`, keep all existing inputs, add blueprint input
- [x] 1.3 Verify `nix develop` works and all existing tools (uv, tailwindcss_4, just) are available, daisyui.css symlink works

## 2. Agent Browser Package

- [x] 2.1 Create `nix/packages/agent-browser.nix` — fetchurl prebuilt binary, autoPatchelfHook, platform lookup table, version variable at top
- [x] 2.2 Add `perSystem.agent-browser` to devshell packages in `nix/devshell.nix`
- [x] 2.3 Verify `nix develop` provides `agent-browser` command and `agent-browser --version` works
