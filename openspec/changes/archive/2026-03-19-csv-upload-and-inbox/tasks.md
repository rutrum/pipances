## 1. Schema Change

- [x] 1.1 Add `marked_for_approval` boolean column (default False) to Transaction model in `models.py`

## 2. Navigation

- [x] 2.1 Create `_navbar.html` partial with DaisyUI navbar — links to /upload and /inbox
- [x] 2.2 Update `base.html` to include the navbar partial
- [x] 2.3 Update index route to redirect to /inbox

## 3. Upload Page

- [x] 3.1 Create upload route (GET /upload) that loads importers and internal accounts, renders upload.html
- [x] 3.2 Create `upload.html` template with importer dropdown, account dropdown, file input, and HTMX form submission
- [x] 3.3 Create upload handler (POST /upload) that parses CSV with selected importer, validates, ingests to DB, and redirects to /inbox. On error, return inline error message.

## 4. Inbox Page

- [x] 4.1 Create inbox route (GET /inbox) that queries pending transactions (joined with accounts), renders inbox.html
- [x] 4.2 Create `inbox.html` template with DaisyUI table — columns: checkbox, date, amount, raw_description, description (editable), external (editable), plus Commit button
- [x] 4.3 Create `_inbox_row.html` partial for a single transaction row (reused for HTMX swaps)

## 5. Inline Editing

- [x] 5.1 Create PATCH /transactions/{id} route that handles updates to description, external account name, and marked_for_approval
- [x] 5.2 Implement click-to-edit for description field — clicking shows input, blur/enter saves via HTMX PATCH, swaps row
- [x] 5.3 Implement click-to-edit for external account field — same pattern, resolves/creates external account on save

## 6. Approval Workflow

- [x] 6.1 Implement approval checkbox — toggles marked_for_approval via HTMX PATCH, row styling changes
- [x] 6.2 Create POST /inbox/commit route — bulk approves all marked transactions, prunes orphaned external accounts, re-renders inbox table

## 7. CSS Build

- [x] 7.1 Rebuild Tailwind CSS to include new DaisyUI classes used in templates (`just css`)

## 8. Verification

- [x] 8.1 Navigate to localhost:8098 in browser, verify navbar appears with Upload and Inbox links
- [x] 8.2 Go to /upload, verify importer and account dropdowns are populated, upload sample.csv, verify redirect to inbox
- [x] 8.3 On /inbox, verify transactions appear in table, test inline editing of description and external account
- [x] 8.4 Test approval checkbox toggles, then commit — verify marked transactions disappear from inbox
- [x] 8.5 Verify empty inbox shows appropriate message with link to upload
