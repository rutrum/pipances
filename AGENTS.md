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
- When a discussion defers a topic for later, add it to `TODO.md` with enough context to pick it up again.

## Self Improvement

If the user corrects you on something, consider adding it to AGENTS.md.  
- But VERIFY WITH THE USER FIRST.  
- Do this alongside the existing conversion.
- Do not suggest an addition or modification in isolation unless its the end of a discussion.
