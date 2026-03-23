## Context

The Settings page is being replaced with a Data page that has a sidebar menu for navigation between sections. This phase creates the layout and migrates existing content (internal accounts, categories, transactions table) into it.

## Goals / Non-Goals

**Goals:**
- Sidebar menu using DaisyUI `menu` component with two sections: Configuration and Data
- HTMX-driven content swaps (click sidebar item, content pane updates)
- Deep-linkable URLs (`/data/accounts`, `/data/transactions`, etc.)
- Migrate internal accounts (editable) and categories (read-only, rename only) from Settings
- Migrate transaction table from the deleted `/transactions` into `/data/transactions`
- Remove category delete functionality

**Non-Goals:**
- External accounts, importers, import history sections (phase 3)
- Any new editing capabilities
- Explore links on entity rows (phase 3)

## Decisions

### DaisyUI sidebar menu with section titles
**Choice:** Use the DaisyUI `menu` component in a vertical layout on the left side. Use `menu-title` class for "CONFIGURATION" and "DATA" section headers. Active item highlighted with DaisyUI's built-in active state.
**Why:** Native DaisyUI component, no custom CSS needed. Supports the grouping and nesting we want. Matches the rest of the UI.

### URL structure: `/data/{section}`
**Choice:** Each section gets a distinct URL path.
```
/data                    → redirects to /data/accounts
/data/accounts           → internal accounts (editable)
/data/importers          → placeholder for phase 3
/data/transactions       → full transaction table
/data/external-accounts  → placeholder for phase 3
/data/categories         → read-only list with rename
/data/imports            → placeholder for phase 3
```
**Why:** Deep-linkable, bookmarkable, works with browser back/forward. The sidebar active state is driven by comparing the current URL path.

### HTMX content pane swap
**Choice:** Each sidebar link has `hx-get="/data/{section}"` targeting a `#data-content` div. The server returns just the content partial when it detects an HTMX request, or the full page (layout + sidebar + content) for a direct navigation.
**Why:** Standard HTMX pattern. Same approach used by the old dashboard tabs. Sidebar stays static, only content changes.

### Layout: fixed sidebar + scrollable content

```
┌────────────────────────────────────────────────────────┐
│  Data                                          [h1]    │
│  ┌──────────────┬─────────────────────────────────┐    │
│  │  CONFIGU-    │                                 │    │
│  │  RATION      │  Content pane                   │    │
│  │              │  (swapped via HTMX)             │    │
│  │  ● Accounts  │                                 │    │
│  │  ○ Importers │  #data-content                  │    │
│  │              │                                 │    │
│  │  DATA        │                                 │    │
│  │              │                                 │    │
│  │  ○ Trans-    │                                 │    │
│  │    actions   │                                 │    │
│  │  ○ External  │                                 │    │
│  │    Accounts  │                                 │    │
│  │  ○ Categories│                                 │    │
│  │  ○ Import    │                                 │    │
│  │    History   │                                 │    │
│  └──────────────┴─────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

Use Tailwind flex layout: sidebar is `w-56 shrink-0`, content is `flex-1 min-w-0`.

### Migrate accounts and categories as-is
**Choice:** The internal accounts table and categories list move into the Data page content pane with minimal changes. Same templates, same edit endpoints (URL paths stay at `/accounts/{id}` and `/categories/{id}` for the API — only the page URLs change).
**Why:** Minimize risk. The existing edit functionality works well. Only the page chrome changes.

### Remove category delete
**Choice:** Remove the delete button from `_category_row.html` and the `DELETE /categories/{id}` endpoint.
**Why:** User decided categories should be read-only for now (rename only). Deleting categories is destructive and not currently useful. Can revisit later (noted in TODO).

### Transaction table in Data page
**Choice:** `/data/transactions` renders the same transaction table as the old `/transactions` page — filters, sorting, pagination, all statuses. No charts.
**Why:** The Data page is for managing/viewing raw data. Charts live in Explore. The table partials are shared between both pages.

### Navbar: "Settings" becomes "Data"
**Choice:** Rename the navbar link. URL changes from `/settings` to `/data`.
**Why:** The page is no longer just settings — it contains read-only data views too. "Data" is short and accurate.

## Risks / Trade-offs

- **[Phase 3 placeholders]** Some sidebar items (Importers, External Accounts, Import History) won't have content yet. Options: hide them until phase 3, or show them with a "Coming soon" message. Lean toward hiding — less confusing.
- **[Route migration]** Changing `/settings/*` to `/data/*` breaks any bookmarks. Acceptable for a single-user self-hosted app.
- **[Sidebar on mobile]** The sidebar layout needs to work on narrow screens. Options: collapse to a horizontal tab bar, use a drawer, or just stack vertically. DaisyUI drawer component could work for mobile. Defer mobile optimization — desktop-first for now.
