## Why

Transactions are currently limited to a single category, but real-world purchases often span multiple spending areas (e.g. a grocery run that's partly food, partly household supplies). This change adds the ability to split a transaction's amount across multiple categories from within the edit modal.

## What Changes

- Add a `transaction_splits` table to store explicit split allocations
- Add a **Splits section** to the transaction edit modal (below the Category field)
- Users can add one or more splits, each with an amount and a category
- The "remainder" (transaction total minus all split amounts) stays assigned to the transaction's primary `category_id`
- Live remainder calculation via Alpine.js; persistence via HTMX
- Splits are validated: each amount > 0, sum of splits < transaction total (remainder must be > 0)
- Category aggregations in stats/charts/filtering are **not** changed — primary category is used as-is (split-aware aggregation is future work)

## Capabilities

### New Capabilities
- `transaction-splits`: Splitting a transaction's amount across multiple categories from the edit modal

### Modified Capabilities
- `inbox-review`: The edit modal gains a new Splits section below the Category field

## Impact

- **New model**: `TransactionSplit` (id, transaction_id, category_id, amount_cents)
- **New DB table**: `transaction_splits` (with migration in `db.py`)
- **New routes**: `POST/PATCH/DELETE /transactions/{id}/splits/{sid?}`
- **New template**: `_splits_section.jinja2`
- **Modified template**: `_transaction_edit_modal.jinja2` — splits section added after Category field
- **New JS dependency**: Alpine.js (for live remainder calculation)
- **No changes** to stats, charts, or category filtering
