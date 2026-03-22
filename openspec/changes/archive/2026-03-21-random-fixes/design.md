## Context

The app has two main table views: inbox (pending transactions) and transactions (approved). The transactions page already has pagination, sorting, and column filtering. The inbox page has filtering but no pagination or sorting, and loads all pending transactions at once. Both pages use HTMX for partial updates but don't preserve filter state in the URL.

Several UI elements use manual Tailwind classes where DaisyUI provides better built-in alternatives, and the ML prediction indicator uses a background color that disrupts layout during editing.

## Goals / Non-Goals

**Goals:**
- Inbox table has pagination and sorting, matching the transactions page patterns
- Filter/sort state survives page refresh on both inbox and transactions
- Cleaner ML indicator that doesn't affect layout
- More polished click-to-edit experience with ghost inputs
- Better DaisyUI class usage throughout (nav active state)
- Right-aligned amount column with consistent decimal alignment

**Non-Goals:**
- Reworking the transactions page table structure (planned separately)
- Shared/reusable sort/pagination partials between inbox and transactions (will duplicate for inbox to keep them independent)
- Adding new filter types to inbox
- Changing the edit/save flow or combo box behavior

## Decisions

### Inbox pagination: dedicated partial
Duplicate `_pagination.html` as `_inbox_pagination.html` with inbox-specific URLs (`/inbox/rows`) and target (`#inbox-table`). The transactions page will be reworked later, so sharing a parameterized partial isn't worth the coupling.

### Inbox sorting: inline in inbox.html
Add sort headers directly in `inbox.html`'s `<thead>` rather than extracting a macro. The inbox sort headers hit `/inbox/rows` and target `#inbox-table`. Sort state is carried via hidden inputs in the filter bar, same pattern as transactions.

### Filter persistence: hx-push-url
Add `hx-push-url="true"` to HTMX requests that change filter/sort/page state. On initial page load, the server reads query params and passes them to the template to pre-populate filter controls and apply the filters to the query.

For inbox, this means `/inbox` accepts the same params as `/inbox/rows` (date_from, date_to, internal_id, import_id, sort, dir, page, page_size) and applies them on GET.

For transactions, `/transactions` already accepts filter params for the HTMX partial; it just needs to also handle them on full page load and add `hx-push-url`.

### ML indicator: absolutely-positioned blue dot
Replace `bg-info/10 rounded px-1` with a structure like:
```html
<span class="relative">
  <span class="absolute -left-3 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-info"></span>
  Field value
</span>
```
The dot sits in the left margin of the cell via absolute positioning, so it doesn't push content. The parent `<td>` needs enough left padding to accommodate the dot. When ml_confidence is null, the dot span is omitted and the field content stays in the same position.

### Click-to-edit: ghost input + italic placeholder
- Empty fields show `<span class="italic text-base-content/40">click to edit</span>` instead of a badge
- The combo box edit input changes from `input input-bordered input-sm` to `input input-ghost input-sm` so it blends with the cell until focused

### Nav active state: DaisyUI active class
Replace `font-bold border-b-2 border-primary text-primary` with DaisyUI's `active` class on the menu `<a>` element, which provides a subtle background highlight consistent with the component library.

### Custom date range: inline layout
Change `_txn_date_range.html` to use a single flex row with `flex-wrap` so the custom date inputs appear to the right of the preset buttons. On narrow screens they wrap below naturally.

## Risks / Trade-offs

- **Duplicated inbox pagination partial** - Small amount of duplication vs coupling to a shared partial that will change when transactions is reworked. Acceptable for now.
- **hx-push-url on every HTMX interaction** - Could lead to noisy browser history. Mitigated by using `hx-push-url` only on the main filter/sort/page controls, not on inline edits or approval toggles.
- **Blue dot absolute positioning** - Requires consistent left padding on cells. If padding varies, dots may overlap content. Mitigated by using a fixed small padding on the relevant `<td>` elements.
