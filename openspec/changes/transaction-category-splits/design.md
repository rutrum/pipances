## Context

Transactions currently carry a single `category_id` FK. Category aggregations in stats, charts, and filtering all operate on that field directly. The transaction edit modal (added in `inbox-transaction-modal-edit`) provides the editing surface.

The existing data model is intentionally flat — `transaction.category_id` is a first-class field, not derived from a child table. Any splits design must preserve that property for the simple (unsplit) case, which is the overwhelming majority of transactions.

## Goals / Non-Goals

**Goals:**
- Allow a transaction to be split across multiple categories from within the edit modal
- Keep the simple case (no splits) zero-overhead — no extra joins required for the 99% case
- Live remainder calculation without a server round-trip on every keystroke
- Persist splits immediately when added or removed (consistent with existing modal behavior)
- Validate that splits cannot consume the entire transaction amount (remainder must remain > 0)

**Non-Goals:**
- Split-aware category aggregations in stats, charts, or filters (future work)
- ML predictions for split categories
- Splitting by external account, description, or any field other than category
- Bulk-splitting multiple transactions at once
- Enforcing that splits sum to exactly the total (remainder is always implicit)

## Decisions

### Decision 1: Schema — Additive extras only (no default row)

**Choice:** `transaction_splits` only contains rows when the user has explicitly split. `transaction.category_id` remains the "remainder" category.

```
transactions:        id, ..., category_id    ← remainder category (unchanged)
transaction_splits:  id, transaction_id, category_id, amount_cents  (NOT NULL)
```

**Rationale:** Keeps the simple case zero-cost. No joins needed when splits don't exist. No "default row" invariant to maintain. `transaction.category_id` retains its current semantics and all existing queries stay unchanged.

**Alternative considered:** Materialize a default split row for every transaction (the user's original idea). Rejected because it requires a DB row per transaction at creation time, complicates queries (always need to join), and adds an invariant (exactly one NULL-amount row per transaction) that must be enforced everywhere.

### Decision 2: Alpine for live remainder, HTMX for persistence

**Choice:** Alpine `x-data` on the splits section tracks `splitAmounts` (a dict keyed by split ID) and `newAmountDollars` (the pending add-split input). Remainder is a computed Alpine property. All server operations (POST create, PATCH update, DELETE remove) are HTMX — each returns the full re-rendered `_splits_section.jinja2` partial. Alpine is already bundled in the project at `/static/js/alpine.min.js`.

**Rationale:** Remainder must update instantly as the user types — a server round-trip per keystroke is too chatty. Alpine handles this with a single computed property. HTMX handles all durable state; Alpine is purely ephemeral UI state.

**Alternative considered:** Pure HTMX with server-rendered remainder on every blur. Rejected because the remainder display lags behind the user's input, making the form feel unresponsive.

### Decision 3: Splits section as a self-contained re-renderable partial

**Choice:** `_splits_section.jinja2` is a `<div id="splits-section-{txn_id}">` that every split mutation endpoint returns as `outerHTML` swap. The partial includes its own `x-data` initialization from server state, so Alpine re-inits cleanly after each swap.

**Rationale:** Consistent with existing OOB/partial patterns in the project. Avoids needing to sync Alpine state with HTMX responses — the server is always the source of truth for persisted splits, Alpine only owns in-flight typing state.

### Decision 4: Amount input in dollars, stored as cents

**Choice:** Amount inputs use `type="number" step="0.01"` (dollar values). The server converts to cents: `amount_cents = round(float(amount_dollars) * 100)`.

**Rationale:** Consistent with how amounts are displayed throughout the app (always formatted as dollars). Avoids exposing cents to the user.

### Decision 5: Add Split requires valid amount only; form is always visible

**Choice:** The add-split form (amount input + category select) is always rendered at the bottom of the splits section. The "Add Split" button is gated by Alpine: disabled until `newAmountCents > 0 AND newAmountCents < (totalCents - savedSum)`. Category is not required to enable the button. Clicking "Add Split" is the only moment a split record is created in the DB.

**Rationale:** No empty DB records, no approval-blocking invariant to enforce server-side. The form inputs are purely ephemeral Alpine state until the button is clicked. This is consistent with the existing modal pattern — combo boxes are always present and only persist on an explicit user action. Category is optional on the new split (matching `transaction.category_id` being nullable) and can be set afterward via the split row's select.

**Alternative considered:** Create an empty split record immediately when "Add Split" is clicked, then block approval if any split has a null amount. Rejected — this requires a new server-side invariant ("no approvable transaction with incomplete splits"), complicates the approval endpoint, and adds DB churn for records that may never be filled in.

**Choice:** The "Add Split" button is `:disabled` via Alpine until `newAmountCents > 0 AND newAmountCents < (totalCents - savedSum)`. The POST endpoint validates the same constraint server-side.

**Rationale:** Prevents orphaned split records with zero or invalid amounts. Simple client-side gate catches the common case; server-side validation is the safety net.

### Decision 6: Category on splits may be NULL

**Choice:** `category_id` on `TransactionSplit` is nullable. No enforcement of non-null at the DB layer.

**Rationale:** Consistent with `transaction.category_id` being nullable. A split without a category is not useful now but doesn't break anything. Future features may attach other metadata to splits.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Alpine re-init wipes in-flight typing state on HTMX swap | Acceptable: only happens after a completed action (Add/Delete), not while typing |
| `amount_dollars` float → cents rounding edge cases | Use `round()` server-side; `step="0.01"` client-side limits input precision |
| Splits ignored in charts/stats silently misleads users | Acceptable for now; future work to add split-aware aggregation |
| Sum of splits could theoretically equal transaction total if PATCH reduces remainder to 0 | Server validates on PATCH: new total must leave remainder > 0 |

## Test Plan

Splits are always manually created by the user via the edit modal — they never arrive from imports. Seed data therefore does not include any `TransactionSplit` records; tests create them as needed.

### Three-layer approach

**Layer 1: API-level tests** (`tests/test_splits.py`)
Fast in-memory DB + HTTPX tests covering every endpoint's happy path and validation errors (POST 422 on zero/excess amount, PATCH 422 on remainder elimination, 404s). A `txn_with_split` fixture creates a transaction + one pre-existing split.

**Layer 2: Story-based UI tests** (`tests/ui/test_transaction_splits.py`)
Given the overhead of live-server + Playwright (seeding, browser launch, page navigation), tests cover entire end-to-end flows rather than isolated assertions. Three stories exercise the full split feature:

- **Story A** — single split lifecycle: add (with Alpine gate on invalid amounts), set category, persist across modal reopen, delete, close with row refresh
- **Story B** — multiple splits + validation: build two splits, hit Alpine gate on exceeded remainder, hit server 422 on PATCH that would eliminate remainder, observe error + revert, recover with valid edit
- **Story C** — three-split buildup: sequential adds verifying remainder math, Alpine gate on 4th, mid-sequence delete recalculation

No seed data carries split records. The `txn_for_splitting` fixture picks a known pending transaction, sets description + external (so the modal is openable and the result is approvable), yields its ID and amount, and cleans up all splits + restores the transaction on teardown.

**Layer 3: Manual smoke-testing**
The existing verification checklist (add/delete split, remainder updates, modal close refresh) covers manual browser testing during development.

## Migration Plan

1. Add `TransactionSplit` model and `transaction_splits` table migration in `db.py` — safe, additive only
2. Existing transactions are unaffected (no splits = full amount in primary category, same as today)
3. No data backfill needed
4. Rollback: drop `transaction_splits` table; remove model, routes, and template includes
