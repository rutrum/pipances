## Context

A comprehensive code review identified critical security, data integrity, and crash bugs across the codebase. This change addresses all critical and high-severity findings that affect correctness and safety. The application is a self-hosted financial tracker with no authentication yet (a separate concern), so the primary risk surface is data corruption and XSS from stored/reflected data.

The codebase currently constructs HTML via Python f-strings in ~10 locations, passes user data into JavaScript/JSON without proper escaping, and lacks input validation on query parameters. These are not theoretical risks -- any account or category name with special characters will trigger them.

## Goals / Non-Goals

**Goals:**
- Eliminate all XSS vectors (f-string HTML, JS interpolation, hx-vals JSON)
- Fix the floating-point currency conversion that loses cents
- Prevent server crashes from invalid input (null checks, int parsing, date parsing)
- Tighten dedup logic to prevent false-positive deduplication
- Enable SQLite foreign key enforcement
- Escape SQL LIKE wildcards in search

**Non-Goals:**
- Authentication/CSRF (tracked in TODO.md as a separate feature)
- Splitting main.py into modules (architectural cleanup, separate change)
- Adding tests (separate change)
- Content-Security-Policy headers (requires auth infrastructure first)
- File upload size limits (needs config design)

## Decisions

### 1. Move f-string HTML to Jinja2 template partials

**Decision**: Create small template partials for each edit widget (edit-name, edit-type, edit-balance, edit-balance-date, edit-description, edit-category-name) instead of constructing HTML in Python f-strings.

**Rationale**: Jinja2 auto-escaping is enabled by default, so moving to templates eliminates the XSS class entirely rather than sprinkling `html.escape()` calls (which are easy to forget).

**Alternative considered**: Using `html.escape()` in f-strings. Rejected because it's error-prone and doesn't solve the structural problem.

### 2. Use `|tojson` filter for JavaScript interpolation

**Decision**: In `inbox.html`, replace bare `{{ value }}` inside `<script>` blocks with `{{ value|tojson }}`, which produces properly JSON-encoded strings including quote escaping.

**Rationale**: This is the standard Jinja2 approach for safely embedding values in JavaScript.

### 3. Build hx-vals dicts in Python, render with `|tojson`

**Decision**: For `_combo_results.html` and `_txn_table_body.html`, pass pre-built dicts from the template context or construct them in Jinja2, then render with `{{ dict|tojson }}`.

**Rationale**: This eliminates the hand-crafted JSON strings that break on special characters.

### 4. Use `int(round(amount * 100))` for currency conversion

**Decision**: Change `ingest.py:102` from `int(row["amount"] * 100)` to `int(round(row["amount"] * 100))`.

**Rationale**: Minimal change that fixes the truncation bug. The schema already uses `Decimal(38, 2)` so the values coming in should have at most 2 decimal places, but the Polars `.to_dicts()` conversion produces Python floats, so `round()` is the correct safety net. This matches the pattern already used in `main.py:468` and `main.py:523`.

### 5. Add internal account to dedup key

**Decision**: Change the dedup key from `(date, amount_cents, description)` to `(date, amount_cents, description, internal_account_name)` and scope the database count query to also filter by `internal_id`.

**Rationale**: Without this, importing the same CSV for two different bank accounts causes false dedup. Adding the internal account to the key is the minimal correct fix.

### 6. Validate query params with helper function

**Decision**: Create a small `_safe_int(value, default, min_val, max_val)` helper and a `_safe_date(value)` helper in `main.py` to wrap `int()` and `date.fromisoformat()` calls.

**Rationale**: Centralizes the pattern rather than adding try/except to every call site.

### 7. Enable FK enforcement via engine event

**Decision**: Use a SQLAlchemy `event.listen(engine.sync_engine, "connect", ...)` callback to execute `PRAGMA foreign_keys = ON` on every new connection, rather than putting it in `create_tables()`.

**Rationale**: The PRAGMA must be set per-connection in SQLite. An event listener ensures it's always on, even for connections not going through `create_tables()`.

## Risks / Trade-offs

- **Dedup key change**: Existing data was deduped with the old key. Re-importing a CSV that was previously deduped could now insert rows that were previously considered duplicates (if the internal account differs). This is the correct behavior but could surprise users who re-import.
  -> Mitigation: This only affects future imports. Existing data is unchanged.

- **Template partial explosion**: Creating 6+ new template partials for edit widgets adds files.
  -> Mitigation: These are small (3-5 lines each) and eliminate an entire class of bugs. They can be consolidated into a macro later.

- **FK enforcement on existing data**: Enabling foreign keys could cause errors if orphaned references exist in the current database.
  -> Mitigation: The orphan pruning in commit_inbox already handles this. We'll enable FK enforcement but not retroactively validate existing data.
