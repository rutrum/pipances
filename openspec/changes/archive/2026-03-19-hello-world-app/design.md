## Context

The project has a working Python package skeleton with uv and a Nix flake (Tailwind v4 standalone CLI). Now we need a running FastAPI app with the full frontend stack: Jinja2 templates, HTMX for interactivity, and Tailwind CSS v4 + DaisyUI v5 for styling.

The Tailwind v4 standalone CLI cannot use `@plugin "daisyui"` (requires node_modules). However, DaisyUI v5 publishes a standalone CSS file that can be `@import`ed alongside Tailwind. We confirmed this works: `@import "tailwindcss"; @import "./daisyui.css";` compiles correctly with the standalone CLI.

## Goals / Non-Goals

**Goals:**
- FastAPI app runnable via `uv run python -m financial_pipeline.main`
- Jinja2 base template with HTMX loaded via CDN
- Tailwind CSS v4 compiled via standalone CLI with DaisyUI v5
- Static file serving for compiled CSS
- A styled index page proving the full stack works

**Non-Goals:**
- No database, models, or business logic
- No authentication
- No hot-reload or watch mode for Tailwind (nice-to-have later)
- No custom Tailwind theme configuration beyond DaisyUI defaults

## Decisions

### DaisyUI v5 CSS as a flake input
The `@plugin` directive requires node_modules, which the standalone CLI doesn't have. Instead, DaisyUI v5's published CSS file is added as a flake input pointing to the jsDelivr URL. The shell hook symlinks it to `./daisyui.css` at the project root. The Tailwind input CSS imports it via `@import "./daisyui.css"`. The symlink is gitignored.

### Tailwind v4 — no config file
Tailwind v4 uses CSS-based configuration (`@import`, `@theme`, `@source`) instead of `tailwind.config.js`. Content paths are specified via `@source` in the input CSS. No JS config file needed.

### File layout
- `src/financial_pipeline/main.py` — FastAPI app, uvicorn runner
- `src/financial_pipeline/templates/base.html` — Jinja2 base template
- `src/financial_pipeline/templates/index.html` — index page extending base
- `static/css/style.css` — compiled CSS output (gitignored), at project root not inside Python package
- `input.css` — Tailwind input at project root (imports tailwindcss + daisyui.css, `@source` points to templates)
- `daisyui.css` — symlink to Nix store (gitignored, created by shell hook)

### HTMX via CDN
HTMX is a single small JS file. CDN is the simplest approach and avoids bundling.

## Risks / Trade-offs

- [DaisyUI CSS version pinned in flake.lock] → Updating requires `nix flake update daisyui-css`. This is fine — it's explicit and reproducible.
- [Tailwind must be rebuilt when templates change] → Manual rebuild for now. A watch command can be added later.
- [Compiled CSS is gitignored] → Must run Tailwind build after checkout. Could commit it instead, but keeping build artifacts out of git is cleaner.
