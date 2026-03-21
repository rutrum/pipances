## Context

The current `flake.nix` uses a manual `forAllSystems` helper with an inline devShell. This works but is boilerplate-heavy and doesn't scale well as we add packages. numtide/blueprint eliminates this by mapping a folder structure to flake outputs automatically. Separately, the Chrome DevTools MCP server has been unreliable for browser automation, so we need `agent-browser` (a Rust CLI from Vercel) available in the devshell.

Current flake structure:
```
flake.nix    # ~33 lines, inline devShell, forAllSystems boilerplate
```

Target structure:
```
flake.nix                        # ~10 lines, just inputs + blueprint call
nix/
├── devshell.nix                 # extracted devShell
└── packages/
    └── agent-browser.nix        # prebuilt binary package
```

## Goals / Non-Goals

**Goals:**
- Migrate to blueprint with `prefix = "nix/"` so Nix files live in a subdirectory (Python-primary repo)
- Package `agent-browser` v0.21.2 prebuilt binary for the devshell
- Support all four platform targets (linux-x64, linux-arm64, darwin-x64, darwin-arm64)
- Keep the `daisyui-css` non-flake input working through the migration

**Non-Goals:**
- Building agent-browser from Rust source (too complex, fragile across updates)
- Packaging Chrome for Testing in Nix (accept impurity: user runs `agent-browser install` once)
- Adding agent-browser as a NixOS module or service

## Decisions

### 1. Use `autoPatchelfHook` for the prebuilt binary

The agent-browser release binaries are standard ELF executables that need the NixOS dynamic linker and library paths patched. `autoPatchelfHook` handles this automatically — it inspects the binary's needed shared libraries and patches the interpreter and rpath.

**Alternative considered:** Manual `patchelf` calls — more verbose, error-prone, and requires knowing exact library deps upfront.

### 2. Platform selection via `stdenv.hostPlatform`

Use a lookup table mapping `system` to the GitHub release asset name and hash. This keeps the package definition clean and supports all four platforms the flake targets.

```
x86_64-linux  → agent-browser-linux-x64
aarch64-linux → agent-browser-linux-arm64
x86_64-darwin → agent-browser-darwin-x64
aarch64-darwin → agent-browser-darwin-arm64
```

### 3. Reference package from devshell via `perSystem`

Blueprint provides `perSystem` to reference packages defined in the same flake. The devshell will use `perSystem.agent-browser` rather than importing the file directly.

### 4. Version as a `let` binding

Put `version = "0.21.2"` at the top of `agent-browser.nix` so bumping is a one-variable change (plus updating hashes).

## Risks / Trade-offs

- **[Impure Chrome dependency]** → Accepted. User runs `agent-browser install` once. Could add a shellHook reminder.
- **[Binary hash changes on version bump]** → Each platform needs its own hash updated. Use `lib.fakeHash` to get the right hash on first build attempt.
- **[Upstream could change release asset naming]** → Low risk for a versioned release. Pin to exact version.
