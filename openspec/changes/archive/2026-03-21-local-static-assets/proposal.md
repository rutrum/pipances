## Why

The app currently loads 6 JavaScript libraries from CDNs (unpkg, jsdelivr). This means the app requires internet access to function, which undermines the self-hosted goal. It also means versions can shift unexpectedly (lucide is pinned to `@latest`), and page loads depend on third-party uptime.

## What Changes

- Add all 6 JS dependencies as Nix flake inputs (`flake = false` file fetches), matching the existing pattern used for `daisyui.css`
- Symlink the fetched files into `static/js/` via the Nix devshell hook
- Update templates to reference local `/static/js/` paths instead of CDN URLs
- Pin all versions explicitly
- Add `static/js/` to `.gitignore`

## External Dependencies

| Package              | Pinned Version | Source URL                                                              |
|----------------------|----------------|-------------------------------------------------------------------------|
| htmx.org             | 2.0.4          | `https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js`                   |
| htmx-ext-resp-targets| 2.0.2          | `https://unpkg.com/htmx-ext-response-targets@2.0.2/response-targets.js`|
| lucide               | 0.577.0        | `https://unpkg.com/lucide@0.577.0/dist/umd/lucide.min.js`              |
| vega                 | 5.33.1         | `https://cdn.jsdelivr.net/npm/vega@5.33.1/build/vega.min.js`           |
| vega-lite            | 5.23.0         | `https://cdn.jsdelivr.net/npm/vega-lite@5.23.0/build/vega-lite.min.js` |
| vega-embed           | 6.29.0         | `https://cdn.jsdelivr.net/npm/vega-embed@6.29.0/build/vega-embed.min.js`|

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None (infrastructure only — same assets served from a different path).

## Impact

- **flake.nix**: 6 new inputs
- **nix/devshell.nix**: Extended shellHook to symlink JS files into `static/js/`
- **base.html**: 3 script src attributes changed from CDN to `/static/js/`
- **dashboard.html**: 3 script src attributes changed from CDN to `/static/js/`
- **.gitignore**: Add `static/js/`
