## Context

Phase 2 created the Data page layout with sidebar. This phase fills in the remaining sections: External Accounts, Importers, Import History. It also adds Explore links to all entity rows (internal accounts, external accounts, categories).

## Goals / Non-Goals

**Goals:**
- External Accounts section: read-only table with name, transaction count, link to Explore
- Importers section: read-only table listing discovered importer files with name and filename
- Import History section: read-only table with institution, filename, timestamp, row count
- Explore links on internal account rows, external account rows, and category rows
- Transaction count column on categories list

**Non-Goals:**
- Editing external accounts (they're auto-created from transactions)
- Editing importers (they're Python files on disk)
- Editing import history
- Pagination on these lists (defer unless lists get long)

## Decisions

### External accounts: query with transaction counts
**Choice:** Query all accounts where `kind='external'`, join with a COUNT of transactions grouped by `external_id`. Display as a simple table with Name, Txn Count, and an Explore link.
**Why:** Gives users a useful overview of where their money goes. The count provides at-a-glance context for which external accounts are most active.

### Importers: scan the `importers/` directory
**Choice:** At request time, scan the `importers/` directory for Python files, import each module, and read its `IMPORTER_NAME` attribute. Display filename and importer name.
**Why:** Importers are defined as Python files with a convention (`IMPORTER_NAME`, `parse()`). No database table needed. Dynamic discovery means adding a new importer file is immediately visible.
**Alternative:** Cache the importer list at startup. Overkill for a handful of files.

### Import history: query the Import table
**Choice:** Query all rows from the `imports` table, ordered by `imported_at` descending. Display institution, filename, timestamp, and row count.
**Why:** Straightforward read from existing data. Users can see what they've imported and when.

### Explore links as icon buttons
**Choice:** Each row in accounts, external accounts, and categories gets a small link/button (Lucide `external-link` or `compass` icon) that navigates to `/explore?{filter}={value}`.
**Why:** Consistent pattern across all entity types. Non-intrusive — doesn't dominate the row. The link uses the entity name as the filter value (matching how Explore filter dropdowns work).

```
Internal account "Chase Checking"  → /explore?internal=Chase+Checking
External account "Walmart"         → /explore?external=Walmart
Category "Groceries"               → /explore?category=Groceries
```

### Categories: add transaction count, keep rename
**Choice:** The categories list gains a "Txn Count" column showing how many transactions use that category. Rename (click-to-edit) stays. No delete, no create (categories are created inline from the transaction table).
**Why:** Count provides useful context. Rename handles typo fixes. Creation happens organically when categorizing transactions.

### Partial templates for each section
**Choice:** Each Data section is a standalone partial template:
- `_data_accounts.html` (migrated from settings_accounts, already exists from phase 2)
- `_data_transactions.html` (migrated from transactions, already exists from phase 2)
- `_data_external_accounts.html` (new)
- `_data_categories.html` (migrated from settings_categories, already exists from phase 2, add count + explore link)
- `_data_importers.html` (new)
- `_data_imports.html` (new)

**Why:** Each partial is loaded into the content pane via HTMX. Self-contained, testable, simple.

## Risks / Trade-offs

- **[Importer discovery at request time]** Scanning the filesystem and importing Python modules on every request is slightly unusual. For 1-5 files it's negligible. If the importers directory grows large, could cache at startup.
- **[No pagination on new sections]** External accounts and import history could grow. For personal finance (tens of external accounts, dozens of imports), a flat list is fine. Add pagination if/when it becomes a problem.
- **[Category create button removed]** Users can only create categories by typing a new name in the transaction table's category field. This is intentional but worth noting — if a user wants to pre-create categories, they'd need to add a transaction first. Could revisit if it becomes a pain point.
