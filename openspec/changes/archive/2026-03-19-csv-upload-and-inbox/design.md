## Context

The app has a working FastAPI server with Jinja2/HTMX/DaisyUI, a database with accounts/imports/transactions, and a CSV parsing pipeline with importer discovery and ingest. Now we need the web UI to tie it all together: upload CSVs and review imported transactions in an inbox.

## Goals / Non-Goals

**Goals:**
- Upload page with importer and account selection
- Inbox page with inline editing, approval marking, and bulk commit
- DaisyUI navbar for navigation
- All interactions via HTMX (no full page reloads for edits/approvals)
- Orphan pruning on commit

**Non-Goals:**
- No transaction browser for approved transactions (next change)
- No pagination or filtering on inbox (keep simple for now)
- No polished layout — functional is enough for testing
- No auth

## Decisions

### Schema change: marked_for_approval boolean
Add `marked_for_approval: bool` column to Transaction model, defaulting to `False`. This is orthogonal to `status` — it's workflow UI state, not data lifecycle. Commit sets `status='approved'` and resets `marked_for_approval=False` for all marked rows.

### Edits auto-save immediately
Each inline edit (description, external account) triggers an HTMX PATCH that saves to the DB immediately. No buffering in the browser. This means:
- User never loses work
- Each edit is a single server round-trip
- "Edited" state is derivable from data (description IS NOT NULL, or external account differs from raw_description)

### External account editing is free text
First pass: free text input. User types an account name. On save, the system finds-or-creates an account with `kind='external'`. Autocomplete/dropdown can come later.

### Orphan pruning happens at commit time
When transactions are committed, any external accounts with `kind='external'` that have zero transaction references are deleted. This cleans up accounts created during import that were reassigned during review.

### HTMX patterns
- **Upload form:** `hx-post="/upload"` with `hx-encoding="multipart/form-data"`. On success, `HX-Redirect` header sends to /inbox. On error, swap error message into the form.
- **Inline edit:** Click cell → `hx-get` loads an input field. Blur/enter → `hx-patch` saves and swaps back to display.
- **Approval checkbox:** `hx-patch` on change, swaps the row to reflect new styling.
- **Commit button:** `hx-post="/inbox/commit"`, re-renders the full table (marked rows disappear).

### Route structure
```
GET  /upload                  Upload page with form
POST /upload                  Process CSV upload, redirect to inbox
GET  /inbox                   Inbox page with pending transactions table
POST /inbox/commit            Bulk approve marked transactions
PATCH /transactions/{id}      Update description, external, or marked_for_approval
```

### Template structure
```
templates/
├── base.html                 Updated: add navbar partial
├── _navbar.html              DaisyUI navbar with Upload, Inbox links
├── upload.html               Upload form
├── inbox.html                Full inbox page
└── _inbox_row.html           Single table row partial (for HTMX swaps)
```

The `_inbox_row.html` partial is reused for both initial render and HTMX swaps — keeps the row markup in one place.

## Risks / Trade-offs

- [No pagination on inbox] → Fine for initial testing with small CSVs. Will need pagination before handling real-sized imports (hundreds of transactions).
- [Free text external account editing] → Risk of typos creating duplicate accounts. Acceptable for first pass; autocomplete is a clear follow-up.
- [HTMX inline editing complexity] → Multiple HTMX swap patterns on one page. Keep the patterns consistent: click-to-edit → input → blur-to-save.
