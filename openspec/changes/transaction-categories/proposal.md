## Why

Transactions currently lack any categorization beyond their external account (which serves as a rough proxy for "where money goes"). Proper categories (groceries, utilities, entertainment, etc.) are needed for meaningful dashboard breakdowns, filtering, and financial insight. Additionally, the inline editing pattern for external accounts uses a plain text input with no autocomplete — building a reusable combo box (search + create inline) for categories gives us the opportunity to retrofit it onto external accounts too, improving the editing UX across the board.

## What Changes

- New `Category` model (id, name) with nullable FK on `Transaction`
- Reusable combo box component: a search-as-you-type dropdown that shows matching existing values and offers inline creation of new ones — replaces the current plain text input pattern
- Inbox editing gains a category column using the combo box
- External account editing in the inbox retrofitted to use the same combo box pattern (replaces current plain text input)
- Categories management page under `/settings/categories` tab for CRUD
- Transaction browsing page gains a category filter dropdown

## Capabilities

### New Capabilities
- `transaction-categories`: Category model, category assignment on transactions, category management CRUD
- `combo-box`: Reusable server-driven search + create-inline component for entity selection (used by categories and external accounts)

### Modified Capabilities
- `inbox-review`: Add category column with combo box editing; retrofit external account editing to use combo box
- `account-management`: Add "Categories" tab to settings page
- `transaction-browsing`: Add category filter to the transactions page

## Impact

- **Models**: New `Category` table, new `category_id` FK column on `transactions` table (nullable)
- **DB migration**: ALTER TABLE for `category_id` on existing transactions, CREATE TABLE for categories
- **Templates**: New combo box partials, modified inbox row, new settings categories tab, modified transaction filters
- **Endpoints**: New search/create endpoints for combo box, new CRUD endpoints for categories management, modified transaction query to include category
- **No breaking changes**: category_id is nullable, existing transactions remain uncategorized until manually assigned
