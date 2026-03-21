## Why

The current UI is functional but visually plain — it uses the generic DaisyUI `light` theme, the navbar has no active page indicator or icons, and there's no user feedback after form submissions. These small gaps make the app feel like a prototype rather than a polished tool. Addressing them now, while the page count is small, is cheaper than retrofitting later.

## What Changes

- Switch DaisyUI theme from `light` to `silk` for a warmer, more refined look
- Add active page highlighting to the navbar so users always know where they are
- Add icons to navbar links via Lucide icon font (CDN)
- Show a badge on the Inbox nav link with the count of pending transactions
- Replace the italic "(click to edit)" placeholder in the inbox with a `badge badge-ghost` for a more intentional, clickable appearance
- Add DaisyUI toast notifications for action feedback after upload success and inbox commit

## Capabilities

### New Capabilities

- `toast-notifications`: Toast-based feedback after user actions (upload, commit)

### Modified Capabilities

- `navigation`: Adding active page indicator, icons, and inbox count badge to the navbar
- `inbox-review`: Changing empty-description placeholder styling from italic text to badge component
- `csv-upload`: Adding success feedback via toast after upload completes

## Impact

- **Templates**: `base.html`, `_navbar.html`, `_inbox_row.html`, `upload.html`, `inbox.html`
- **Backend routes**: All route handlers pass `active_page` to template context; `shared_context()` helper injects `inbox_count` into every response
- **CDN dependency**: Lucide icons added via CDN script tag
- **Inbox badge live update**: Commit response includes OOB swap to update the navbar badge count without full page reload
