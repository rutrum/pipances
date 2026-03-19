## Context

Previous experience with financial CSV analysis showed that normalizing transactions into a unified schema with `internal`/`external` account references is more useful for analysis than a `source`/`destination` model with always-positive amounts. The app's inbox review flow means users manually normalize messy bank data before approval, which enables a unified accounts table for both owned and external accounts.

## Goals / Non-Goals

**Goals:**
- Async SQLite via SQLAlchemy + aiosqlite
- Three tables: `accounts`, `imports`, `transactions`
- Tables auto-created on app startup
- Seed internal accounts from a user-managed Python config module

**Non-Goals:**
- No migrations framework (Alembic) yet — tables are created fresh
- No CSV parsing or import logic (next change)
- No inbox UI or approval flow (later change)

## Decisions

### Unified accounts table for internal and external
A single `accounts` table holds both the user's accounts (checking, savings, credit_card, liability) and external parties (merchants, payees, employers). The `kind` column distinguishes them:
- `checking`, `savings`, `credit_card`, `liability` → user-owned
- `external` → merchants, payees, etc.

This was chosen over separate tables because:
- Internal-to-internal transfers (checking → savings) are clean: both FKs point to the same table, no special casing
- The inbox review step normalizes messy bank strings into clean account names before approval, so external account quality is user-controlled
- Orphaned external accounts (created during import, then reassigned during review) are pruned automatically

### Signed amounts stored as integer cents
`amount_cents` is a signed integer: negative means money left the internal account, positive means money entered it. Stored as cents (multiply by 100) to avoid SQLite's lack of native DECIMAL and to enable numeric operations in raw SQL. `SUM(amount_cents)` grouped by internal account gives the net balance change directly. Display logic divides by 100.

### Transaction type is computed, not stored
Type (withdrawal, deposit, transfer) is derivable:
- External account `kind = 'external'` + amount < 0 → withdrawal
- External account `kind = 'external'` + amount > 0 → deposit
- External account `kind != 'external'` → transfer

No need to store this in the DB. It can be computed in queries or as a Python property.

### Transaction status for inbox flow
Transactions have a `status` field: `pending` (in inbox, awaiting review) or `approved` (reviewed and accepted). Both live in the same table — the inbox is just a filtered view. This avoids a staging table and means pending transactions are already available for analysis.

### Import tracking table
Each CSV upload creates an `imports` row recording the institution, filename, timestamp, and row count. Transactions reference their import via FK. This enables:
- Undo-ing an import (delete all transactions from import N)
- Tracking when data was imported
- Knowing which institution a record came from

### Dual description columns
`raw_description` stores the original bank CSV text (never modified). `description` is nullable, defaulting to NULL — the user fills it in during inbox review. The frontend falls back to `raw_description` when `description` is NULL.

### User-managed Python config module
Internal accounts are defined in a user-managed Python module at `src/config/` (gitignored), because this module will eventually also contain CSV parsing schemas/cleaning pipelines for each institution. Exact structure of the API between `config` and `financial_pipeline` is deferred (see TODO.md). For now, seeding is a placeholder that creates a few example accounts.

### Orphan pruning
When a user reassigns a transaction's external account during inbox review (e.g. from "WALMART SUPERCENTER #3521" to "Walmart"), the old auto-created account may become orphaned. External accounts with zero transaction references are pruned after review actions.

## Schema

```
┌──────────────────────────┐
│ accounts                 │
├──────────────────────────┤
│ id        INTEGER PK     │
│ name      TEXT UNIQUE     │
│ kind      TEXT NOT NULL   │
│   checking               │
│   savings                │
│   credit_card            │
│   liability              │
│   external               │
└──────────┬───────────────┘
           │
     ┌─────┴──────┐
     │             │
     ▼             ▼
┌──────────────────────────────────────────┐
│ transactions                             │
├──────────────────────────────────────────┤
│ id              INTEGER PK               │
│ import_id       FK → imports             │
│ internal_id     FK → accounts            │
│ external_id     FK → accounts            │
│ raw_description TEXT NOT NULL             │
│ description     TEXT (nullable, user set) │
│ date            DATE NOT NULL             │
│ amount_cents    INTEGER NOT NULL          │
│ status          TEXT NOT NULL             │
│   pending                                │
│   approved                               │
└──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ imports                             │
├─────────────────────────────────────┤
│ id            INTEGER PK            │
│ institution   TEXT NOT NULL          │
│ filename      TEXT                   │
│ imported_at   TIMESTAMP NOT NULL     │
│ row_count     INTEGER               │
└─────────────────────────────────────┘
```

## Risks / Trade-offs

- [Orphaned external accounts accumulate between prune cycles] → Acceptable; pruning is cheap and can run after each review action.
- [No Alembic migrations] → Fine for early development. Schema changes mean dropping and recreating. Alembic can be added before the app holds real data.
- [Integer cents loses sub-cent precision] → Bank transactions are always whole cents. Not an issue for this use case. The Polars ingest layer will need to convert `Decimal(38,2)` → integer cents.
