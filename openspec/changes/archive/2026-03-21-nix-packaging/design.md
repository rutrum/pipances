## Context

The app currently runs only from the source tree via `uv run`. Static JS files are symlinked from flake inputs by the devshell hook. CSS is built via `tailwindcss` at dev time. Importers are discovered from a `PROJECT_ROOT/importers/` directory. All path resolution uses `Path(__file__).resolve().parent.parent.parent` to find the project root.

For production packaging, these paths won't exist in the same structure. We need the Nix package to bundle everything into a self-contained unit.

## Goals / Non-Goals

**Goals:**
- `nix build` produces a runnable package with all deps, static assets, and built CSS
- `nix build .#docker` produces a Docker container image loadable with `docker load`
- Keep `uv` as the sole tool for managing Python dependencies
- Keep the dev workflow unchanged (`nix develop` + `uv run`)

**Non-Goals:**
- NixOS module (systemd service, nginx config, etc.) — future work
- Multi-architecture Docker images
- Optimizing Docker image layer size beyond what `buildLayeredImage` gives us

## Decisions

### 1. Use uv2nix for Python dependency resolution

uv2nix parses `uv.lock` at Nix evaluation time (pure Nix, no network). Each locked dependency becomes a Nix derivation. Use `sourcePreference = "wheel"` to avoid needing build overrides for most packages.

Required flake inputs:
- `pyproject-nix` (core Python-in-Nix library)
- `uv2nix` (lockfile parser)
- `pyproject-build-systems` (pre-packaged build backends)

**Alternative considered**: Fixed-output derivation running `uv sync` — requires network in sandbox, less reproducible.

### 2. Static assets bundled at build time

The Nix package derivation will:
1. Copy JS files from flake inputs into `static/js/`
2. Run `tailwindcss` to build CSS from `input.css` + `daisyui.css` into `static/css/style.css`
3. Include the `static/` directory in the final package

This happens in a wrapper derivation that combines the uv2nix virtualenv with the static assets.

### 3. Path resolution via environment variables

Currently `main.py` and `ingest.py` resolve paths via `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent`. This breaks when installed as a package.

Add environment variable overrides with fallback to current behavior:
- `FINANCIAL_PIPELINE_STATIC_DIR` — path to `static/` directory (default: `PROJECT_ROOT / "static"`)
- `FINANCIAL_PIPELINE_IMPORTERS_DIR` — path to `importers/` directory (default: `PROJECT_ROOT / "importers"`)
- `FINANCIAL_PIPELINE_DB_PATH` — path to SQLite database file (default: `financial_pipeline.db` in cwd)

The Nix wrapper script sets these env vars pointing to the correct Nix store paths.

### 4. Docker image via `buildLayeredImage`

Use `pkgs.dockerTools.buildLayeredImage` which creates efficient layer caching. The image contains:
- The uv2nix virtualenv (Python + all deps)
- Static assets (JS + built CSS)
- A wrapper script as the entrypoint that sets env vars and runs uvicorn

The image exposes port 8098 and expects a volume mount for the SQLite database.

### 5. Package structure

```
nix/packages/
├── financial-pipeline.nix   — the main app package
└── docker.nix               — the Docker image
```

The app package is a derivation that:
1. Takes the uv2nix virtualenv
2. Adds a `static/` directory with JS + built CSS
3. Includes the `importers/` directory
4. Wraps `uvicorn` with correct env vars and module path

### 6. Keep devshell separate from uv2nix

The existing devshell uses `uv` to manage the venv at dev time. This is fine — uv2nix is only for the production build. The devshell continues to use `uv sync` and the `shellHook` symlinks for static assets.

## Risks / Trade-offs

- **uv2nix overrides**: Some Python packages may need build system overrides. `sourcePreference = "wheel"` minimizes this. If a dep doesn't have a wheel, we may need to add an override. The `pyproject-build-systems` input provides common build backends.
- **Tailwind in Nix sandbox**: `tailwindcss` needs to scan template files to know which classes to include. The templates must be available in the build derivation. This should work since we're copying from the source tree.
- **Importers as external plugins**: Currently importers live in the repo root. For production, they're bundled into the package. Future: could make importers dir configurable at runtime for user-defined importers.
