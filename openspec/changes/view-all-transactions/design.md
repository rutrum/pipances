## Context

The app currently has an upload page and an inbox page for reviewing pending transactions. Once transactions are approved via the inbox commit workflow, there's no way to view them. This change adds a read-only transactions page with server-side filtering, sorting, and pagination — all driven by HTMX with no client-side state.

The existing inbox table is purpose-built for editing (checkboxes, click-to-edit fields). This page is read-only and introduces reusable partials (date range widget, pagination controls) designed for reuse on future pages like account drill-downs.

## Goals / Non-Goals

**Goals:**
- Browse all approved transactions with pagination
- Filter by date range (presets + custom), internal account, external account
- Sort by any column (click column header to toggle)
- Reusable partials: `_date_range.html`, `_pagination.html`
- All state in query params — bookmarkable, no JS state

**Non-Goals:**
- Editing transactions from this page (that's the inbox)
- Full-text search on descriptions (future enhancement)
- Infinite scroll (using page numbers)
- Refactoring the inbox to share components (deferred, see TODO.md)

## Decisions

### Server-side filtering, sorting, and pagination
**Choice:** All table interactions are server-side via HTMX round-trips.
**Why:** We paginate anyway so the data isn't all on the client. Personal finance datasets are small enough (hundreds to low thousands of rows) that server round-trips are fast. This keeps the architecture consistent with HTMX-everywhere and avoids shipping a JS table library.
**Alternative:** Client-side JS table (e.g. AG Grid, Tabulator). Rejected — adds JS dependency, fights the HTMX approach, overkill for this dataset size.

### HTMX state management via hidden inputs
**Choice:** A wrapping `<form>` contains hidden inputs for all current filter/sort/page state. Each interactive control (sort header, filter, pagination) uses `hx-include` to carry all state on every request. The server returns the `<tbody>` + pagination controls as a partial.
**Why:** Keeps all state declarative in the DOM. No JS variables to manage. Each HTMX request carries the full query context.
**Alternative:** URL query params via `hx-push-url`. Could layer this on later for bookmarkability, but hidden inputs are simpler to start with.

### Date range widget as a reusable partial
**Choice:** `_date_range.html` is a self-contained Jinja partial. Presets (YTD, Last Month, Last 3 Months) are a DaisyUI `join` button group. Clicking a preset fires an HTMX request immediately. "Custom" toggles open two `<input type="date">` fields with an Apply button.
**Why:** Date filtering by time window is the most common query pattern for financial data. Presets reduce friction for the 80% case. The partial can be dropped into any page that needs time filtering.

### Column header auto-filter dropdowns
**Choice:** Account columns (internal, external) have a small filter icon in the header. Clicking it toggles a dropdown with account names as checkboxes/options. Selecting filters and clicking away applies the filter via HTMX.
**Why:** Spreadsheet-style filtering is familiar UX. Keeps filters visually compact inside the table header rather than a separate filter bar.
**Implementation:** A DaisyUI `dropdown` component nested in the `<th>`. Contains a list of account names as links/buttons that set hidden input values and trigger an HTMX request.

### Pagination with page numbers
**Choice:** Traditional prev/next with page indicator and configurable page size (25/50/100). Default 25 rows per page.
**Why:** Predictable, simple, works well with server-side approach. Page size selector lets users adjust for their screen/preference.

### Single GET endpoint with query params
**Choice:** `GET /transactions` serves both the full page (initial load) and the partial table update (HTMX requests). Differentiate via `HX-Request` header — full page returns `transactions.html`, HTMX request returns just the table body + pagination partial.
**Why:** Single endpoint, single query-building function. The HTMX partial response is a subset of the full page response.

## Risks / Trade-offs

- **[Column filter dropdowns could get long]** → If there are many external accounts, the dropdown list gets unwieldy. Mitigation: for now, just list all; later add a search/filter within the dropdown.
- **[No URL bookmarkability initially]** → State is in hidden inputs, not the URL. Mitigation: can add `hx-push-url` later to sync state to URL params.
- **[Date presets assume timezone]** → "YTD" and "Last Month" are computed server-side based on server time. Mitigation: acceptable for a single-user self-hosted app.
