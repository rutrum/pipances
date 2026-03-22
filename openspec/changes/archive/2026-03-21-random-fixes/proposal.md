## Why

The inbox and transactions pages have accumulated several UI/UX rough edges: the inbox lacks pagination and sorting, filters are lost on page refresh, the ML indicator styling is heavy-handed and breaks layout on edit, click-to-edit fields have misaligned padding, and the nav bar uses manual styling instead of DaisyUI's built-in classes. These are all small individually but together make the app feel unpolished.

## What Changes

- **Inbox pagination**: Add page/page_size support to the inbox rows endpoint, with a dedicated pagination partial for inbox
- **Inbox sorting**: Add sortable column headers (Date, Amount, Description) to the inbox table
- **Filter persistence on refresh**: Add `hx-push-url` to HTMX requests on both transactions and inbox pages so URL reflects filter state; server reads query params on initial page load
- **Amount column cleanup**: Remove `$` from cell values (keep in header), right-align amount cells so decimal points line up; applies to both inbox and transaction rows
- **ML indicator rework**: Replace `bg-info/10` background with a small absolutely-positioned blue dot that doesn't affect layout; dot disappears when user edits the value
- **Click-to-edit improvements**: Replace `badge-ghost` placeholder with plain italic grey text; switch inline edit input from `input-bordered` to `input-ghost` for seamless appearance
- **Nav bar active state**: Replace manual `border-b-2 border-primary text-primary` with DaisyUI's built-in menu active class
- **Custom date filter positioning**: Lay out the custom date inputs inline to the right of the preset buttons instead of below them

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `inbox-review`: Add pagination and sorting requirements; update placeholder styling to italic grey text; update ML indicator to blue dot; update amount display format
- `inbox-filtering`: Add filter persistence via URL state on page refresh
- `transaction-browsing`: Add filter persistence via URL state on page refresh; update amount display format; update custom date range layout to inline
- `navigation`: Update active page indicator to use DaisyUI built-in styling instead of manual classes

## Impact

- **Templates**: `_inbox_row.html`, `_txn_row.html`, `_navbar.html`, `_txn_date_range.html`, `inbox.html`, `transactions.html`, `_combo_edit.html`; new `_inbox_pagination.html` and inbox sort headers
- **Backend**: `/inbox/rows` endpoint gains sort/page/page_size params; `/inbox` and `/transactions` endpoints read filter state from URL query params on initial load
- **No database changes**
- **No new dependencies**
