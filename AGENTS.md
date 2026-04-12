# Pipances

## Goals

I need a self hosted finances app that can help me track finances and visualize my expenses.

- load transactions dumps as csvs
- parse those csvs using defined polars expressions
- redundancy checking: transactions that are the same are discarded as already prcessed
- transactions are aligned to a fixed number of "sources" that I own: bank accounts, liabilities, credit cards
- web interface that allows me to 
  - upload transaction csvs into an "inbox" for review
  - review the inbox transactions in a table/grid
  - mark transactions as "human approved" where they are no longer in inbox
  - view all transactions
  - see a variety of statistics and graphs based on my transactions
- simple web login (single user, views all data)

## Non Goals

Some features I don't want for an initial release, despite them being good ideas.

- downloading/fetching transactions from banking institutions
- defining custom transaction schemas in the UI
- machine learning for auto filling in descriptions
- semantic search
- defining source accounts in the web UI

# Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| UI interactivity | HTMX |
| Templating | Jinja2 |
| CSS framework | Tailwind CSS + DaisyUI |
| Data processing | Polars |
| Visualization | Altair (Vega-Lite) |
| Database | SQLite (via aiosqlite) |
| ORM | SQLAlchemy (async) |
| Auth | Simple session-based (single user) |
| Python packaging | uv |
| System packaging | Nix flake (wraps uv) |

## Python Dependencies

- `fastapi` + `uvicorn[standard]` — web server
- `jinja2` — templates
- `python-multipart` — file uploads
- `polars` — data transforms
- `altair` — charts
- `aiosqlite` — async SQLite driver
- `sqlalchemy[asyncio]` — async ORM
- `itsdangerous` — session signing for auth

## Frontend

- HTMX — loaded via CDN
- Tailwind CSS — standalone CLI (no Node.js required)
- DaisyUI — Tailwind plugin for component classes (btn, card, table, modal, etc.)

## DaisyUI Best Practices

**Use DaisyUI components as-is — do NOT override with custom Tailwind classes unless absolutely necessary and user-confirmed.**

- DaisyUI components are designed with proper spacing, alignment, and responsive behavior built-in
- Only add custom Tailwind classes to DaisyUI components when:
  1. The desired behavior is explicitly missing from DaisyUI
  2. The user confirms the visual need (via screenshot/browser testing)
  3. Standard DaisyUI classes don't provide the required functionality
- Examples of what NOT to do:
  - ❌ Adding `items-center` to `form-control` — the component handles alignment correctly by default
  - ❌ Adding custom padding/margins to `btn` — use DaisyUI's `btn-sm`, `btn-lg`, `btn-xl` variants instead
  - ❌ Customizing `select`, `input`, `textarea` directly — use DaisyUI variants like `input-bordered`, `select-primary`
- Default DaisyUI structure works: `<div class="form-control w-full"><label class="label"><span class="label-text">...</span></label><select class="select select-bordered w-full">...</select></div>`

# Agent Preferences

- Do NOT write bash statements over multiple lines; use && or ; instead
- Do NOT use hyphens for printing in bash, use equal signs instead (i.e. echo "===")
- Prefer `jq` over `python -c "import json;..."`
- If you mention multiple statements/ideas that the user will respond to, number them if possible to keep things easy to match with.
- Use `podman` instead of `docker` for container operations

## Build and Run

- Use `just --list` to see available build/test/run commands before guessing
- Common recipes: `just serve` (dev server on 8098), `just css` (build CSS), `just css-watch` (watch mode), `just sync` (install deps)
  - If just serve fails because the port is taken, that likely means that the hot-reloaded server is already running, and you may continue.
- Test data: `just seed` (resets DB and populates with deterministic test data via `scripts/seed.py`), `just reset-db` (deletes DB only)
- After `just seed`, the server must be restarted to pick up the new database file
- `test_export.csv` in project root contains April 2026 data for testing the CSV import workflow
- Code quality recipes: `just lint` (check Python + templates), `just fmt` (auto-format Python + templates), `just check` (CI-style strict check)
- Run `just fmt` after making changes to keep formatting consistent
- Ruff handles Python linting/formatting; djLint handles Jinja2/HTML templates
- UI regression tests: `just test-ui` (Playwright, must run via `nix develop`); unit tests: `just test`

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

**Rule of Thumb:** Templates always include `hx-swap-oob` attributes. No conditional parameters. Buttons that trigger OOB-only responses use `hx-target="none"` and `hx-swap="none"`.

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
        hx-target="none"
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

- When creating new `.nix` files, always `git add` them before running `nix build` or `nix flake show` — blueprint silently ignores untracked files
- Before writing Nix package files, read the blueprint skill for the correct function signature and conventions

## SQLAlchemy and SQLite

- `Base.metadata.create_all` only creates NEW tables — it does NOT add new columns to existing tables
- When adding columns to existing models, add `ALTER TABLE` statements in `create_tables()` in `db.py`, using `PRAGMA table_info(tablename)` to check if the column already exists before altering
- Always use `server_default` on new columns so existing rows get a value

## Task Deferral

Whenever the user mentions something as "TODO" or "we'll handle that later" etc, add that idea to TODO.md.
- When a discussion defers a topic for later, add it to `TODO.md` with enough context to pick it up again.
- When completing a change, review `TODO.md` and remove any items that were addressed by the change.

## OpenSpec Preferences

- When making design decisions or large changes AFTER apply, its CRITICAL to update the change artifacts to match the new requirements and design decisions
- Specs should capture END USER BEHAVIOR.  Specs should not capture internal facing changes, tooling, or deployment changes.
  - **When a change has no new or modified capabilities (e.g., refactoring), omit the specs directory entirely.** Code reorganization, template consolidation, and other internal changes don't need specs. No README, no placeholder file — just don't create the directory. The proposal and design are enough.

## Git Operations

**NEVER COMMIT or PUSH. Ever.** Git operations are handled by the user. Your job is to:
- Stage files when asked: `git add <files>`
- Keep uncommitted changes ready for the user to review
- Leave all commit/push decisions to the user

## Self Improvement

If the user corrects you on something, consider adding it to AGENTS.md.  
- But VERIFY WITH THE USER FIRST.  
- Do this alongside the existing conversion.
- Do not suggest an addition or modification in isolation unless its the end of a discussion.
