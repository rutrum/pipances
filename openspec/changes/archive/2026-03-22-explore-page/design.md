## Context

The app has a Dashboard page (charts + stats, three tabs) and a Transactions page (filtered/sorted/paginated table). These are being merged into a single Explore page where filters and date range control both charts and the table simultaneously.

## Goals / Non-Goals

**Goals:**
- Single page combining stats, charts, and transaction table
- All content responds to the same filters (internal account, external account, category) and date range
- Deep-linkable via query parameters
- Reuse existing chart functions and transaction table partials
- Show all transactions (approved + pending)

**Non-Goals:**
- New chart types (reuse the existing three: monthly income/expenses, top expenses, weekly spending)
- Clickable chart elements that apply filters (deferred, already in TODO)
- Account balance calculation (was dashboard-specific, may revisit later)

## Decisions

### Single unified route at `/explore`
**Choice:** One GET endpoint that renders stats, charts, and a transaction table, all filtered by the same query params.
**Why:** Eliminates the mental split between "analysis" and "data browsing." Every filter interaction updates the whole page.
**Alternative:** Keep dashboard and transactions separate but add cross-links. Rejected — doesn't solve the core UX problem.

### Same chart set regardless of filters
**Choice:** Always render the same three charts (monthly income/expenses, top expenses, weekly spending) on whatever data matches the current filters.
**Why:** Simpler to implement and reason about. A monthly income/expenses chart filtered to "Groceries" still makes sense — it shows grocery spending over time. No need for conditional chart selection logic.
**Alternative:** Swap chart types based on filter context (e.g., show account balance chart when filtering by internal account). Rejected for now — adds complexity, can revisit later.

### Show all transaction statuses
**Choice:** The Explore page shows both approved and pending transactions.
**Why:** User wants a unified view of all data. Status can be indicated visually in the table. Charts already computed from whatever data is present.
**Alternative:** Only show approved (like the old dashboard). Rejected per user preference.

### HTMX partial updates for filter changes
**Choice:** When any filter, date range, or pagination control changes, HTMX fetches a partial that includes the stats + charts + table body. An OOB swap updates the date range buttons to reflect active state.
**Why:** Matches the existing pattern used in both dashboard and transactions. Avoids full page reloads.

### Reuse `_txn_table_body.html` and chart functions
**Choice:** The explore page reuses the existing `_txn_table_body.html` partial (with `_txn_row.html`, `_pagination.html`) for the transaction table, and the existing `charts.py` functions for chart generation.
**Why:** These already work well. The explore page just feeds them filtered data.

### Delete old routes, keep edit endpoints
**Choice:** Delete `GET /dashboard`, `GET /dashboard/content`, `GET /transactions`. Keep all `PATCH /transactions/{id}` and edit endpoints since they're used by the inbox and will be used by `/data/transactions` in phase 2.
**Why:** Clean break. No backwards compatibility needed (single user, self-hosted).

### Page layout

```
┌─────────────────────────────────────────────────────────────┐
│  Explore                                           [h1]     │
│                                                             │
│  [YTD] [3mo] [6mo] [1yr] [All] [Custom __|__]    [row]     │
│                                                             │
│  [Account ▼]  [External ▼]  [Category ▼]         [row]     │
│                                                             │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │ Income   │ Expenses │ Net      │ Count    │   [stats]   │
│  └──────────┴──────────┴──────────┴──────────┘             │
│                                                             │
│  ┌────────────────────────────────────────────┐             │
│  │         Monthly Income/Expenses            │   [chart]   │
│  └────────────────────────────────────────────┘             │
│  ┌─────────────────────┐ ┌────────────────────┐             │
│  │  Top Expenses       │ │  Weekly Spending   │   [charts]  │
│  └─────────────────────┘ └────────────────────┘             │
│                                                             │
│  ┌────────────────────────────────────────────┐             │
│  │  Transaction Table (paginated, sortable)   │   [table]   │
│  └────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### Data flow

```
Request: GET /explore?internal=Chase&preset=ytd
                │
                ▼
┌──────────────────────────────────┐
│ Parse query params:              │
│   preset, date_from, date_to    │
│   internal, external, category  │
│   sort, dir, page, page_size    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Query transactions with filters  │
│ (reuse pattern from dashboard +  │
│  transactions routes)            │
└──────────────┬───────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐ ┌──────────────┐
│ All matching │ │ Paginated    │
│ txns → DF    │ │ subset for   │
│ → charts.py  │ │ table        │
└──────┬───────┘ └──────┬───────┘
       │                │
       ▼                ▼
┌──────────────────────────────────┐
│ Template context:                │
│   stats, chart specs, txns,     │
│   filter values, pagination     │
└──────────────────────────────────┘
```

Note: charts are computed from ALL matching transactions (not just the current page). The table shows the paginated subset.

## Risks / Trade-offs

- **[Memory for charts + table]** Charts need all matching transactions loaded into a Polars DF. For personal finance this is fine (thousands of rows). The table query adds a second DB hit with LIMIT/OFFSET. Could optimize with a single query later if needed.
- **[Losing dashboard tab-specific features]** The old dashboard had account balance calculation and account-specific charts (monthly balance, top externals per account). These are dropped for now in favor of the uniform chart set. Can be revisited if missed.
- **[HTMX partial size]** The partial includes stats + three chart specs + table HTML. Could be large. Mitigation: chart specs are compact JSON; table is paginated (25 rows default).
