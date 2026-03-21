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

# Agent Preferences

When speaking with the user
- If you mention multiple statements/ideas that the user will respond to, number them if possible to keep things easy to match with.
- Do NOT use hyphens for printing in bash, use equal signs instead (i.e. echo "===")

## Build and Run

- Use `just --list` to see available build/test/run commands before guessing
- Common recipes: `just serve` (dev server on 8097), `just css` (build CSS), `just css-watch` (watch mode), `just sync` (install deps)
- Code quality recipes: `just lint` (check Python + templates), `just fmt` (auto-format Python + templates), `just check` (CI-style strict check)
- Run `just fmt` after making changes to keep formatting consistent
- Ruff handles Python linting/formatting; djLint handles Jinja2/HTML templates

## Browser Testing

- Utilize the agent-browser skill when testing in the browser
- Always verify UI changes with testing via agent-browser
- Save screenshots to /tmp/agent-browser
- Always run agent-browser via `nix develop -c agent-browser ...` to ensure Chrome's shared libraries are available
- Use `snapshot -i -C` (with `-C`) to get refs for cursor-interactive elements like clickable spans (e.g. click-to-edit fields)
- Chain commands with `&&` when you don't need intermediate output: `nix develop -c agent-browser open <url> && nix develop -c agent-browser wait --load networkidle && nix develop -c agent-browser screenshot`
- Prefer `ref=eN` selectors (from snapshot) over CSS text selectors for clicking — CSS `:text()` selectors often fail for dynamic content
- After typing into a form field, use snapshot to verify the value landed, then click submit via ref
- For HTMX-driven pages, add `sleep 0.5` or `wait --load networkidle` after interactions that trigger HTMX requests before taking screenshots

## HTMX Conventions

- Use the `response-targets` extension (`hx-target-422="#error-div"`, etc.) for directing error responses to a different target. Don't roll custom OOB error handling for this.
- The extension is loaded globally in `base.html` via `hx-ext="response-targets"` on `<body>`
- When HTMX can't handle an interaction (e.g. arrow key navigation), use minimal inline `<script>` in the partial. Keep JS self-contained in an IIFE. Bridge to HTMX by triggering clicks on elements that carry `hx-*` attributes, rather than making fetch calls from JS.
- For cancel/revert on Escape or blur, use PATCH with empty values to re-render the row (the existing PATCH endpoint returns the full row partial).

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

## Self Improvement

If the user corrects you on something, consider adding it to AGENTS.md.  
- But VERIFY WITH THE USER FIRST.  
- Do this alongside the existing conversion.
- Do not suggest an addition or modification in isolation unless its the end of a discussion.
