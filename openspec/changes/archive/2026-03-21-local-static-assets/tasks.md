## 1. Add Flake Inputs

- [x] 1.1 Add 6 new `flake = false` inputs to `flake.nix` with pinned version URLs: htmx-js, htmx-response-targets-js, lucide-js, vega-js, vega-lite-js, vega-embed-js
- [x] 1.2 Run `nix flake update` (or lock the new inputs) to populate `flake.lock`

## 2. Symlink in DevShell

- [x] 2.1 Extend `shellHook` in `nix/devshell.nix` to create `static/js/` and symlink all 6 JS files with readable names

## 3. Update Templates

- [x] 3.1 Update `base.html` to reference `/static/js/htmx.min.js`, `/static/js/response-targets.js`, and `/static/js/lucide.min.js` instead of CDN URLs
- [x] 3.2 Update `dashboard.html` to reference `/static/js/vega.min.js`, `/static/js/vega-lite.min.js`, and `/static/js/vega-embed.min.js` instead of CDN URLs

## 4. Gitignore

- [x] 4.1 Add `static/js/` to `.gitignore`

## 5. StaticFiles Symlink Fix

- [x] 5.1 Enable `follow_symlink=True` on FastAPI `StaticFiles` mount in `main.py` (Starlette rejects symlinks resolving outside the static root by default)

## 6. Verify

- [x] 6.1 Re-enter `nix develop`, confirm symlinks exist in `static/js/`
- [x] 6.2 Run `just serve` and verify all pages load correctly with local assets (no CDN requests)
