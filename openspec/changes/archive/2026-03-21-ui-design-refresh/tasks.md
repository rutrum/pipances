## 1. Theme Switch

- [x] 1.1 Change `data-theme="light"` to `data-theme="silk"` in `base.html`
- [x] 1.2 Verify dashboard charts render correctly against the silk background

## 2. Icons (Lucide CDN)

- [x] 2.1 Add Lucide CDN script tag to `base.html` and call `lucide.createIcons()` on page load and after HTMX swaps
- [x] 2.2 Replace inline SVG icon macro usage in `_navbar.html` with Lucide `<i data-lucide="...">` elements
- [x] 2.3 Remove `_icon.html` partial (no longer needed)

## 3. Navbar Active Page

- [x] 3.1 Create `shared_context(active_page, session)` async helper in `main.py` that returns `{"active_page": active_page, "inbox_count": count}`
- [x] 3.2 Update all route handlers to merge shared context via `ctx |= await shared_context(...)`
- [x] 3.3 Update `_navbar.html` to apply `active` class to the menu item matching `active_page`

## 4. Navbar Inbox Badge

- [x] 4.1 Add inbox count query (COUNT of pending transactions) to `shared_context`
- [x] 4.2 Update `_navbar.html` to show a `badge badge-sm` on the Inbox link when `inbox_count > 0`

## 5. Inbox Empty Description Styling

- [x] 5.1 Replace the italic "(click to edit)" in `_inbox_row.html` with a `badge badge-ghost badge-sm` element

## 6. Toast Notifications

- [x] 6.1 Add `<div id="toast-container" class="toast toast-end toast-bottom"></div>` to `base.html`
- [x] 6.2 Add a small inline script or CSS for toast auto-dismiss (fade out after ~4 seconds)
- [x] 6.3 Upload success: update upload route to redirect to `/inbox?toast=upload_success`, render toast server-side on inbox page load when query param is present
- [x] 6.4 Commit success: return toast HTML as OOB swap (`hx-swap-oob`) in the commit response, showing count of committed transactions
- [x] 6.5 Commit empty: return a warning toast via OOB swap when no transactions were marked

## 7. Inbox Badge Live Update

- [x] 7.1 Add an `id` to the inbox badge element in `_navbar.html` so it can be targeted by OOB swap
- [x] 7.2 Update commit response in `main.py` to include OOB swap HTML that updates the badge count

## 8. Verification

- [x] 8.1 Browse all pages and confirm icons render via Lucide, active states, and badges work
- [x] 8.2 Test inbox commit and confirm badge count updates live, success/warning toasts work
