# Pipances Template & Route Map

Generated 2026-04-08. This document maps every template, partial, and API endpoint.

---

## Page Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           base.html                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ _navbar.html                                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Import   │  │  Inbox   │  │ Explore  │  │      Data        │   │
│  │          │  │          │  │          │  │  (sidebar+panel) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ #toast-container                                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Shared / Global Templates

| Template | Description | Used By |
|---|---|---|
| `base.html` | Layout shell: `<head>`, HTMX, Lucide, toast container | All 4 pages extend it |
| `_navbar.html` | Top nav bar with links to Import, Inbox, Explore, Data + inbox badge | Included by `base.html` |
| `_badge.html` | Inbox count badge (OOB swap target) | `inbox.py` (after commit/retrain) |
| `_toast.html` | Toast notification (OOB swap into `#toast-container`) | `inbox.py` (multiple places) |
| `_pagination.html` | Reusable pagination (prev/next, page size select). Parameterized via Jinja vars: `pagination_url`, `pagination_target`, `pagination_include`, `pagination_id` | Inbox, Explore, Data/Transactions |
| `_edit_input.html` | Generic inline edit `<input>` that PATCHes on blur/Enter. Params: `field_name`, `endpoint`, `target`, `value` | Data/Accounts (name, type, balance, date), Data/Categories (name), Transactions (description) |
| `_combo_edit.html` | Autocomplete combo box for inline editing. Fetches suggestions from `/api/combo/{entity}`, submits via PATCH | Transactions (category, external, description-combo) |
| `_combo_results.html` | Dropdown results for combo box | `widgets.py` → `/api/combo/{entity}` |
| `_txn_row.html` | Read-only transaction row: date, amount, description, category, external, internal | Explore table, Data/Transactions table |

---

## 2. Import Page

**Full page:** `import.html` → extends `base.html`

```
import.html
├── Tab bar: [CSV Upload] [Manual Entry]
└── #import-content ← swapped by tab clicks
    ├── _import_csv.html      (CSV upload form)
    │   └── #csv-preview ← swapped by form submit
    │       └── _import_preview.html  (detected importers, preview table, commit form)
    └── _import_manual.html   (manual entry form)
```

### Templates

| Template | Description | Rendered By |
|---|---|---|
| `import.html` | Full page with tab bar, embeds `import_content_html` | `GET /import` |
| `_import_csv.html` | File upload form → posts to `/import/preview` | `GET /import` (pre-rendered), `GET /import/csv` |
| `_import_manual.html` | Manual entry form (account, date, amount, description, etc.) | `GET /import/manual` |
| `_import_preview.html` | Shows detected importers, transaction preview table, account picker, commit button | `POST /import/preview`, `POST /import/preview/dedup` |

### Routes (`routes/import_page.py`)

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `GET` | `/import` | Full page | Import page with CSV tab active |
| `GET` | `/import/csv` | Partial | CSV upload form (tab swap) |
| `GET` | `/import/manual` | Partial | Manual entry form (tab swap) |
| `POST` | `/import/preview` | Partial | Parse CSV, show preview + importer matches |
| `POST` | `/import/preview/dedup` | Partial | Re-render preview after dedup toggle |
| `POST` | `/import/commit` | Redirect | Commit CSV import → redirect to inbox |
| `POST` | `/import/manual` | Redirect/Error | Commit manual entry → redirect to inbox |

---

## 3. Inbox Page

**Full page:** `inbox.html` → extends `base.html`

```
inbox.html
├── #commit-dialog-container ← receives _commit_summary.html
├── #inbox-message
├── #filter-bar (date range, account, import selects + hidden sort/dir/page)
├── #bulk-toolbar (bulk description, category, external inputs + apply/approve)
├── <table class="table table-fixed w-full">
│   ├── <thead> ← includes _inbox_thead.html
│   │   └── _inbox_thead.html (sortable column headers with manual HTMX)
│   └── <tbody id="inbox-table"> ← HTMX swap target
│       └── _inbox_row.html × N (per transaction)
├── #inbox-pagination ← includes _pagination.html
└── <script> (bulk selection logic, toolbar updates, fetch-based bulk PATCH)
```

### Templates

| Template | Description | Rendered By |
|---|---|---|
| `inbox.html` | Full page: filters, bulk toolbar, table, pagination, bulk JS | `GET /inbox` (full page load) |
| `_inbox_thead.html` | Sort headers with hardcoded per-column HTMX (no macro) | Included by `inbox.html`, OOB-swapped by `GET /inbox` (HTMX) |
| `_inbox_row.html` | Editable row: checkbox, date+account, amount, description (click→combo), category (click→combo), external (click→combo), approve button. Supports OOB swap. | `GET /inbox` (HTMX), `PATCH /transactions/{id}`, `PATCH /transactions/bulk`, `POST /inbox/commit`, `POST /inbox/retrain` |
| `_commit_summary.html` | Modal dialog: shows count, new categories, new externals, confirm button | `GET /inbox/commit-summary` |

### Routes (`routes/inbox.py`)

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `GET` | `/inbox` | Full page OR partial (rows + thead + pagination OOB) | List inbox transactions with filters/sort/pagination |
| `GET` | `/inbox/commit-summary` | Partial (modal) | Preview what commit will create |
| `POST` | `/inbox/commit` | Partial (rows + badge + toast OOB) | Move approved txns out of inbox |
| `POST` | `/inbox/retrain` | Partial (rows + toast OOB) | Re-run prediction on inbox txns |

### Cross-router routes used by Inbox

| Method | Path | Router | Returns | Purpose |
|---|---|---|---|---|
| `PATCH` | `/transactions/{id}` | `transactions.py` | `_inbox_row.html` | Inline edit single field |
| `PATCH` | `/transactions/bulk` | `transactions.py` | Multiple `_inbox_row.html` (OOB) | Bulk edit fields |
| `GET` | `/transactions/{id}/edit-description` | `transactions.py` | `_edit_input.html` | Click-to-edit description |
| `GET` | `/transactions/{id}/edit-description-combo` | `transactions.py` | `_combo_edit.html` | Click-to-edit description (combo) |
| `GET` | `/transactions/{id}/edit-category` | `transactions.py` | `_combo_edit.html` | Click-to-edit category |
| `GET` | `/transactions/{id}/edit-external` | `transactions.py` | `_combo_edit.html` | Click-to-edit external |
| `GET` | `/api/combo/{entity}` | `widgets.py` | `_combo_results.html` | Autocomplete suggestions |

---

## 4. Explore Page

**Full page:** `explore.html` → extends `base.html`

```
explore.html
├── _explore_date_range.html (preset buttons: All, YTD, 30d, 90d, 1y, Custom)
├── Hidden inputs: #explore-filters (sort, dir, page, category, external, internal)
└── #explore-content ← HTMX swap target
    └── _explore_content.html
        ├── Stats row (income, expenses, net, count)
        ├── Charts (category pie, monthly bar) via Altair
        ├── {% include "_explore_table.html" %}
        │   ├── Jinja macros: sort_header(), filter_header()
        │   ├── <thead> with macro-generated sortable/filterable headers
        │   ├── <tbody> with _txn_row.html × N
        │   └── _pagination.html
        └── (empty state if no data)
```

### Templates

| Template | Description | Rendered By |
|---|---|---|
| `explore.html` | Full page: date range bar, hidden filter state, explore-content div | `GET /explore` (full page) |
| `_explore_date_range.html` | Preset date buttons (All/YTD/30d/90d/1y/Custom) + custom date inputs. OOB-swappable. | `GET /explore` (embedded + OOB on HTMX) |
| `_explore_content.html` | Stats row + charts + includes `_explore_table.html` | `GET /explore` (HTMX partial or embedded) |
| `_explore_table.html` | Table with Jinja macros for sort/filter headers + `_txn_row.html` rows + pagination. Defines `sort_header()` and `filter_header()` macros. | Included by `_explore_content.html` |

### Routes (`routes/explore.py`)

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `GET` | `/explore` | Full page OR partial (`_explore_content.html` + OOB date range) | View all committed transactions with filters/sort/charts |

---

## 5. Data Page

**Full page:** `data.html` → extends `base.html`

```
data.html
├── Sidebar menu (Accounts, Importers, Transactions, Categories, External Accounts, Imports)
└── #data-content ← swapped by sidebar clicks
    ├── _data_accounts.html
    │   ├── _account_row.html × N (click-to-edit name, type, balance, date)
    │   └── _account_input_row.html (new account form row)
    ├── _data_categories.html
    │   └── _category_row.html × N (click-to-edit name, link to explore)
    ├── _data_transactions.html (has its own sort_header/filter_header macros!)
    │   ├── Date range presets + filters
    │   ├── _txn_row.html × N
    │   └── _pagination.html
    ├── _data_external_accounts.html (read-only table, link to explore)
    ├── _data_importers.html (read-only table)
    └── _data_imports.html (read-only table)
```

### Templates

| Template | Description | Rendered By |
|---|---|---|
| `data.html` | Full page: sidebar nav + `#data-content` panel. Embeds `data_content_html`. | All `GET /data/*` routes (full page) |
| `_data_accounts.html` | Accounts table with show-closed toggle + create row | `GET /data/accounts` |
| `_account_row.html` | Account row with click-to-edit fields (name, type, balance, date) | `GET /data/accounts`, `PATCH /accounts/{id}`, `POST /data/accounts` |
| `_account_input_row.html` | New account input row at bottom of table | `GET /data/accounts` |
| `_data_categories.html` | Categories table | `GET /data/categories` |
| `_category_row.html` | Category row with click-to-edit name + explore link | `GET /data/categories`, `PATCH /categories/{id}` |
| `_data_transactions.html` | Transaction table with its OWN `sort_header`/`filter_header` macros (duplicated from explore), date presets, filters, pagination | `GET /data/transactions` |
| `_data_external_accounts.html` | Read-only external accounts table + explore links | `GET /data/external-accounts` |
| `_data_importers.html` | Read-only importers table | `GET /data/importers` |
| `_data_imports.html` | Read-only import history table | `GET /data/imports` |

### Routes (`routes/data.py`)

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `GET` | `/data` | Redirect → `/data/accounts` | Default data section |
| `GET` | `/data/accounts` | Full page or partial | List internal accounts |
| `POST` | `/data/accounts` | Partial (new row) | Create account |
| `PATCH` | `/accounts/{id}` | Partial (row) | Update account field |
| `GET` | `/accounts/{id}/edit-name` | `_edit_input.html` | Inline edit |
| `GET` | `/accounts/{id}/edit-type` | `_edit_input.html` | Inline edit |
| `GET` | `/accounts/{id}/edit-balance` | `_edit_input.html` | Inline edit |
| `GET` | `/accounts/{id}/edit-balance-date` | `_edit_input.html` | Inline edit |
| `GET` | `/data/categories` | Full page or partial | List categories |
| `PATCH` | `/categories/{id}` | Partial (row) | Update category name |
| `GET` | `/categories/{id}/edit-name` | `_edit_input.html` | Inline edit |
| `GET` | `/data/transactions` | Full page or partial | List all transactions |
| `GET` | `/data/external-accounts` | Full page or partial | List external accounts |
| `GET` | `/data/importers` | Full page or partial | List importers |
| `GET` | `/data/imports` | Full page or partial | List import history |

---

## 6. Shared Widget Routes (`routes/widgets.py`)

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `GET` | `/api/combo/{entity}` | `_combo_results.html` | Autocomplete for category/external/description |

## 7. Transaction Routes (`routes/transactions.py`)

These are entity-level routes used by both Inbox and (potentially) other pages:

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `PATCH` | `/transactions/bulk` | OOB `_inbox_row.html` × N | Bulk update fields |
| `PATCH` | `/transactions/{id}` | `_inbox_row.html` | Update single transaction |
| `GET` | `/transactions/{id}/edit-description` | `_edit_input.html` | Plain text edit |
| `GET` | `/transactions/{id}/edit-description-combo` | `_combo_edit.html` | Combo edit |
| `GET` | `/transactions/{id}/edit-external` | `_combo_edit.html` | Combo edit |
| `GET` | `/transactions/{id}/edit-category` | `_combo_edit.html` | Combo edit |

---

## 8. Root Route (`main.py`)

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `GET` | `/` | Redirect → `/explore` | Default landing page |

---

## Observations

### Duplication

1. **`sort_header` macro is defined THREE times** — once in `_explore_table.html`, once in `_data_transactions.html`, and the inbox has no macro at all (hand-coded per column in `_inbox_thead.html`).

2. **`filter_header` macro is defined TWICE** — in `_explore_table.html` and `_data_transactions.html`. They're nearly identical except for the `hx-get` URL and `hx-target`.

3. **Date range presets duplicated** — `_explore_date_range.html` and `_data_transactions.html` both have preset button rows (All/YTD/30d/90d/1y/Custom) with almost identical markup.

4. **`_txn_row.html` is read-only** — used in Explore and Data/Transactions. But Inbox uses `_inbox_row.html` which is a completely different, editable row. The transaction routes (`PATCH /transactions/{id}`) always return `_inbox_row.html`, meaning they're tightly coupled to the inbox view.

### Architectural Patterns

5. **Dual-mode routes** — Most `GET` routes detect HTMX via headers and return either a full page (with base.html) or just the partial. This is good. Data page and Import page both use the `content_html` variable pattern described in AGENTS.md.

6. **OOB swaps are scattered** — `_badge.html`, `_toast.html`, `_inbox_thead.html`, `_explore_date_range.html` all do OOB swaps. The inbox route manually concatenates HTML strings with OOB rows + pagination + thead + toast + badge.

7. **The transactions router is inbox-specific** — Despite living in its own file (`transactions.py`), every route returns `_inbox_row.html`. If you wanted inline editing in Explore or Data/Transactions, these routes wouldn't work.

### Template Hierarchy

```
base.html
├── _navbar.html
│   └── _badge.html (OOB)
│
├── import.html
│   ├── _import_csv.html
│   │   └── _import_preview.html
│   └── _import_manual.html
│
├── inbox.html
│   ├── _inbox_thead.html
│   ├── _inbox_row.html ──────────────────┐
│   ├── _commit_summary.html              │ shared editing widgets
│   └── _pagination.html                  │
│                                         │
├── explore.html                          │
│   ├── _explore_date_range.html          │
│   └── _explore_content.html             │
│       └── _explore_table.html           │
│           ├── _txn_row.html             │
│           └── _pagination.html          │
│                                         │
├── data.html                             │
│   ├── _data_accounts.html               │
│   │   ├── _account_row.html             │
│   │   └── _account_input_row.html       │
│   ├── _data_categories.html             │
│   │   └── _category_row.html            │
│   ├── _data_transactions.html           │
│   │   ├── _txn_row.html                 │
│   │   └── _pagination.html              │
│   ├── _data_external_accounts.html      │
│   ├── _data_importers.html              │
│   └── _data_imports.html                │
│                                         │
├── _edit_input.html ◄────────────────────┤ used by data + transactions
├── _combo_edit.html ◄────────────────────┤ used by transactions (inbox only)
├── _combo_results.html ◄────────────────┘  used by widgets
└── _toast.html (OOB)
```

### Coupling Issues

```
                    ┌──────────────────┐
                    │  transactions.py  │
                    │                  │
  PATCH /txns/{id} ─┤ always returns   │
  PATCH /txns/bulk ─┤ _inbox_row.html  │──── tightly coupled to inbox
                    │                  │
                    └──────────────────┘
                            │
                            ▼
        Can't reuse for editing in Explore or Data/Transactions
        without returning a different row template
```

### The Three Table Flavors

| Aspect | Inbox | Explore | Data/Transactions |
|---|---|---|---|
| Row template | `_inbox_row.html` (editable) | `_txn_row.html` (read-only) | `_txn_row.html` (read-only) |
| Sort headers | Hand-coded per `<th>` | `sort_header()` macro | `sort_header()` macro (copy) |
| Filter headers | None (uses filter bar above) | `filter_header()` macro | `filter_header()` macro (copy) |
| Date presets | None (date inputs in filter bar) | `_explore_date_range.html` | Inline in template |
| Pagination | `_pagination.html` | `_pagination.html` | `_pagination.html` |
| Stats/Charts | No | Yes | No |
| Bulk actions | Yes (toolbar) | No | No |
| Inline editing | Yes (combo boxes) | No | No |
| Table layout | `table-fixed` with `w-[%]` | Auto width | Auto width |
