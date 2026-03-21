## Context

Transactions currently have no categorization. External accounts serve as a rough proxy, but they represent counterparties, not spending types. The inbox editing UX uses plain text inputs for description and external account — no autocomplete or inline creation affordance.

The current data model:
- `Transaction` has `internal_id` and `external_id` FKs to `Account`
- External accounts are auto-created during CSV ingest via `_resolve_account()`
- Inline editing uses click-to-edit spans that swap to `<input>` elements via HTMX

The settings page has a tab layout with a single "Accounts" tab.

## Goals / Non-Goals

**Goals:**
- Add a `Category` model and nullable FK on transactions
- Build a reusable combo box component (search + inline create) for entity selection
- Use the combo box for both category and external account editing in the inbox
- Add a categories management tab under settings
- Add category filter to the transactions browsing page

**Non-Goals:**
- Hierarchical/nested categories (flat list only)
- Dashboard category breakdowns (deferred)
- Auto-categorization or ML suggestions
- Bulk category assignment
- Category colors, icons, or other metadata beyond name

## Decisions

### Decision: Flat category model with just `name`
Categories are `(id, name)` with unique constraint on name. No color, icon, or sort_order fields. These can be added later if needed.

**Alternative**: Include color for chart segments now. Rejected because dashboard category breakdowns are deferred, so color has no consumer yet.

### Decision: Nullable FK on Transaction
`category_id` is a nullable FK to `categories`. Null means "uncategorized." This avoids needing a sentinel "Uncategorized" category and lets the system work naturally with existing data.

**Alternative**: Required FK with a default "Uncategorized" category. Rejected because it conflates "not yet categorized" with an actual category choice.

### Decision: Combo box as HTMX component with minimal JS for keyboard nav
The combo box works as follows:
1. Click on cell → HTMX GET swaps in a text input with a results dropdown container
2. User types → `hx-trigger="input changed delay:200ms"` fires `hx-get` to a search endpoint
3. Server returns up to 5 filtered matches + a "Create [query]" option at the bottom if no exact match exists
4. User selects via mouse click or keyboard → triggers an `hx-patch` on the transaction to assign the value
5. If "Create new" is selected → server creates the entity and assigns it in one step
6. Blur without selection or Escape → reverts to the previous value (consistent with existing edit pattern)

**Keyboard interaction**: Arrow Up/Down moves a highlight through the dropdown options (with wrap-around). Enter confirms the highlighted option. Escape cancels. This requires a small inline `<script>` or event listener on the combo box container — pure HTMX can't handle arrow key navigation of a list. The JS is minimal: it manages a highlight index, listens for keydown events, and on Enter triggers a click on the highlighted option's element (which has the HTMX attributes for the PATCH). No framework needed.

The search endpoint is generic: `GET /api/combo/{entity}?q=...` where entity is `categories` or `external-accounts`. It returns at most 5 matches. This keeps the server-side reusable.

**Alternative**: Native `<datalist>` element. Rejected because styling is browser-dependent, no "Create new" affordance, and inconsistent cross-browser behavior.

**Alternative**: Fully client-side JS combobox. Rejected because it contradicts the HTMX-first architecture and adds unnecessary JS complexity. The minimal JS needed for arrow key nav is acceptable.

### Decision: Combo box assignment via transaction PATCH
When a user selects a combo box option, it triggers the existing `PATCH /transactions/{txn_id}` endpoint with the appropriate field. For categories, this means adding `category` or `category_id` handling to `update_transaction()`. For external accounts, the existing `external` field handling already works.

For "Create new" in the combo box: the server creates the entity (category or external account) and assigns it to the transaction in a single request via the same PATCH endpoint. The PATCH handler detects whether the value is an existing ID or a new name and acts accordingly.

### Decision: Categories management mirrors accounts management
The `/settings/categories` page follows the same pattern as `/settings/accounts`: a table with inline editing and an input row at the bottom for creating new categories. Since categories only have a `name` field, this is simpler than accounts.

### Decision: Retrofit external account editing to combo box
The current external account cell uses a plain text input. It will be replaced with the combo box component. The `_resolve_account()` function already handles find-or-create semantics, so the backend change is minimal — the improvement is in the UX (showing matching accounts as you type).

## Risks / Trade-offs

- **Combo box complexity**: More moving parts than a simple input or select. Mitigated by keeping it server-driven (no client JS beyond HTMX) and testing with agent-browser.
- **Blur handling**: The combo box needs to distinguish "blur because user clicked an option" from "blur because user clicked away." HTMX's event timing should handle this — the option click fires before the input blur. If not, a short delay on blur handling may be needed.
- **Category deletion with FK references**: If a user deletes a category that's assigned to transactions, we need to decide behavior. Plan: set `category_id = NULL` on affected transactions (SET NULL cascade), keeping them as "uncategorized."

## Migration Plan

1. Add `categories` table via `Base.metadata.create_all` (handles new tables automatically)
2. Add `category_id` column to `transactions` via ALTER TABLE in `create_tables()` with PRAGMA check
3. No data migration needed — all existing transactions start as uncategorized (NULL)
4. Rollback: drop the `category_id` column and `categories` table (though SQLite makes column drops awkward — acceptable since this is a single-user app)
