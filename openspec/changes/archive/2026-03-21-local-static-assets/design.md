## Context

The project uses a Nix flake for system tooling. DaisyUI CSS is already fetched as a `flake = false` file input and symlinked into the project root via `shellHook`. The app serves static files from `static/` via FastAPI's `StaticFiles` mount.

## Goals / Non-Goals

**Goals:**
- Serve all JS dependencies locally — no CDN requests at runtime
- Pin every dependency to an exact version
- Use the existing `flake = false` input pattern for all fetches
- Keep `static/js/` out of git (symlinks to Nix store)

**Non-Goals:**
- Bundling or minification (serve the pre-built min files from npm)
- Moving `daisyui.css` — it's a Tailwind build input, not a served asset, so it stays in the project root

## Decisions

### 1. Flake inputs for JS files

**Decision**: Each JS file becomes a separate `flake = false` input with a pinned version URL.

**Rationale**: Matches the existing daisyui-css pattern. Nix handles fetching, hashing, and caching. The `flake.lock` pins the exact content hash, so builds are reproducible. Updating a version means changing the URL and running `nix flake update <input-name>`.

### 2. Symlink destination: `static/js/`

**Decision**: Symlink all JS files into `static/js/` in the shellHook, using readable filenames.

**Mapping**:
```
${inputs.htmx-js}             → static/js/htmx.min.js
${inputs.htmx-response-targets-js} → static/js/response-targets.js
${inputs.lucide-js}           → static/js/lucide.min.js
${inputs.vega-js}             → static/js/vega.min.js
${inputs.vega-lite-js}        → static/js/vega-lite.min.js
${inputs.vega-embed-js}       → static/js/vega-embed.min.js
```

**Rationale**: FastAPI already serves `static/` via `StaticFiles`. Placing JS alongside CSS in the static tree means templates reference them as `/static/js/filename.js`. The `static/js/` directory is gitignored since it contains only Nix store symlinks.

### 3. Input naming convention

**Decision**: Use `<package>-js` suffix to distinguish from potential future non-JS inputs (e.g., `htmx-js`, `vega-js`).

**Rationale**: Keeps flake inputs self-documenting. The `-js` suffix parallels the existing `-css` suffix on `daisyui-css`.

### 4. StaticFiles follow_symlink

**Decision**: Enable `follow_symlink=True` on the FastAPI `StaticFiles` mount.

**Rationale**: Starlette's `StaticFiles` resolves symlinks and checks that the resolved path is within the static directory root. Symlinks to `/nix/store/` escape this check and return 404. The `follow_symlink=True` parameter disables this containment check, allowing Nix store symlinks to be served. This is safe because the symlinks are created by our own shellHook, not user-controlled.

## Risks / Trade-offs

- **More flake inputs = slower `nix flake update`**: 6 extra file fetches. Negligible in practice.
- **Manual version bumps**: No auto-update. This is intentional — reproducibility over convenience.
- **`nix develop` required to populate `static/js/`**: If someone runs the app without the Nix shell, the JS files won't exist. This matches the existing requirement (daisyui.css also requires `nix develop`). The `just setup` recipe already assumes Nix shell context.
