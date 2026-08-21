# Pipances

A self hosted personal finances app, with a focus on machine learning automation with mandatory human approval.

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python |
| Web server | FastAPI |
| UI interactivity | HTMX |
| Templating | Jinja2 |
| CSS framework | Tailwind CSS + DaisyUI |
| Data processing | Polars |
| Visualization | Altair (Vega-Lite) |
| Database | SQLite (via aiosqlite) |
| ORM | SQLAlchemy (async) |
| Python packaging | uv |
| System packaging | Nix flake (wraps uv) |

## Development practices

- prefer in nearly all cases to use a pre-made DaisyUI class before custom styling with tailwindcss
- refer to the daisy UI skill when considering styling
- prefer out of the box DaisyUI styling before adding additional classes
- add specificity on user request

## Build and Run and Lint

- Use `just --list` to see available build/test/run commands
- Do not run individual linting tools: run `just lint` only

## Browser Testing

- Utilize the agent-browser skill when testing in the browser
- Always verify UI changes with testing via agent-browser
- Save screenshots to /tmp/agent-browser
- Always run agent-browser via `nix develop -c agent-browser ...` to ensure Chrome's shared libraries are available
- Use `snapshot -i -C` (with `-C`) to get refs for cursor-interactive elements like clickable spans (e.g. click-to-edit fields)
- Chain commands with `&&` when you don't need intermediate output: `nix develop -c agent-browser open <url> && nix develop -c agent-browser wait --load networkidle && nix develop -c agent-browser screenshot`
- Prefer `ref=eN` selectors (from snapshot) over CSS text selectors for clicking — CSS `:text()` selectors often fail for dynamic content
- Refs often fail for HTMX-attributed links (e.g. sidebar `<a hx-get="...">`) — fall back to `eval 'document.querySelector("a[hx-push-url=\"/data/foo\"]").click()'` for these
- After typing into a form field, use snapshot to verify the value landed, then click submit via ref
- For HTMX-driven pages, add `sleep 0.5` or `wait --load networkidle` after interactions that trigger HTMX requests before taking screenshots
- In Playwright tests (`tests/ui/`), prefer `expect(locator).to_be_visible()` over `page.wait_for_load_state("networkidle")` — `expect` polls until the specific element changes, which is faster and more expressive than waiting for all network activity to settle

## HTMX Conventions

- Use the `response-targets` extension (`hx-target-422="#error-div"`, etc.) for directing error responses to a different target. Don't roll custom OOB error handling for this.
- The extension is loaded globally in `base.html` via `hx-ext="response-targets"` on `<body>`
- When HTMX can't handle an interaction (e.g. arrow key navigation), use minimal inline `<script>` in the partial. Keep JS self-contained in an IIFE. Bridge to HTMX by triggering clicks on elements that carry `hx-*` attributes, rather than making fetch calls from JS.
- For cancel/revert on Escape or blur, use PATCH with empty values to re-render the row (the existing PATCH endpoint returns the full row partial).
- For layout pages with swappable content (e.g. Data page sidebar): use `{{ data_content_html | safe }}` in the layout template, not `{% block %}`. Pre-render the partial in the route and pass it as a context variable. This way the same partial works for both HTMX swaps (returned directly) and full-page renders (embedded in the layout).

### Out-of-Band (OOB) Swap Pattern

**Rule of Thumb:** Templates always include `hx-swap-oob` attributes. No conditional parameters. Buttons that trigger OOB-only responses use only `hx-swap="none"` (do NOT use `hx-target="none"` — HTMX cannot resolve `none` as a CSS selector and will abort the request).

**Why:**

- Buttons that target a DOM element with `hx-target="#elem"` destroy that element during the `innerHTML` swap before OOB elements can be processed
- This breaks any OOB swaps targeting descendants of the destroyed element
- Result: rows disappear, records vanish, state gets lost

**Pattern:**

Template (`_inbox_row.html`):

```html
<tr id="txn-{{ txn.id }}" hx-swap-oob="outerHTML:#txn-{{ txn.id }}">
  <!-- row content -->
</tr>
```

Button (`inbox.html`):

```html
<button class="btn btn-secondary"
        hx-post="/inbox/retrain"
        hx-swap="none">Retrain</button>
```

Endpoint (`inbox.py`):

```python
rows = ""
for txn in pending:
    rows += templates.get_template("_inbox_row.html").render({"txn": txn})
toast = templates.get_template("_toast.html").render({...})
return HTMLResponse(rows + toast)  # No special parameters, no string manipulation
```

**Anti-patterns to avoid:**

- ❌ Conditional `oob` parameter: `render({"txn": txn, "oob": True})` — adds state management burden
- ❌ Post-render string manipulation: `row_html.replace('id="', 'id="txn-123" hx-swap-oob="..."')` — breaks when templates change
- ❌ Hand-constructed HTML with OOB: `f'<tr hx-swap-oob="...">{...}</tr>'` — loses template ownership, hard to style

**Key insight:** HTMX ignores `hx-swap-oob` on initial page load (only processes it from responses). So templates can unconditionally include it without side effects.

## Nix

- When creating new `.nix` files, always `git add` them before running `nix build` or `nix flake show` or they will not be part of the build
- Before writing Nix package files, read the blueprint skill for the correct function signature and conventions

## SQLAlchemy and SQLite

- `Base.metadata.create_all` only creates NEW tables — it does NOT add new columns to existing tables
- When adding columns to existing models, add `ALTER TABLE` statements in `create_tables()` in `db.py`, using `PRAGMA table_info(tablename)` to check if the column already exists before altering
- Always use `server_default` on new columns so existing rows get a value
