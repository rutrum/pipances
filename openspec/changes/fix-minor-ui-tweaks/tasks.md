## 1. Fix: Account Dropdown Vertical Centering

### Phase 1: Validate the Problem

- [ ] 1.1 Navigate to http://localhost:8098/import/manual
- [ ] 1.2 Take screenshot showing the account dropdown misalignment
- [ ] 1.3 Note in screenshot: dropdown appears lower than label text
- [ ] 1.4 Save screenshot as `before-dropdown-centering.png`

### Phase 2: Implement the Fix

- [ ] 1.5 Open `src/pipances/templates/_import_manual.html`
- [ ] 1.6 Locate the form-control div wrapping the select (around line 12)
- [ ] 1.7 Add `items-center` class to the parent div to vertically center children
- [ ] 1.8 Verify file saved

### Phase 3: Validate the Fix

- [ ] 1.9 Refresh browser at http://localhost:8098/import/manual
- [ ] 1.10 Take screenshot showing corrected alignment
- [ ] 1.11 Note in screenshot: dropdown and label are now vertically aligned
- [ ] 1.12 Save screenshot as `after-dropdown-centering.png`
- [ ] 1.13 Compare before/after screenshots side-by-side

---

## 2. Fix: Keyboard Navigation - Skip Checkboxes in Tab Order

### Phase 1: Validate the Problem

- [ ] 2.1 Navigate to http://localhost:8098/inbox
- [ ] 2.2 Place cursor in the browser address bar
- [ ] 2.3 Press Tab repeatedly to cycle through interactive elements
- [ ] 2.4 Observe that the focus lands on row checkboxes before editable fields
- [ ] 2.5 Note: After checkbox, Tab goes to next row instead of moving to description/category/external fields
- [ ] 2.6 Record observation: "Checkboxes interrupt tab flow through editable fields"

### Phase 2: Implement the Fix

- [ ] 2.7 Open `src/pipances/templates/_inbox_row.html`
- [ ] 2.8 Find the checkbox input (class="checkbox select-txn")
- [ ] 2.9 Add `tabindex="-1"` attribute to remove from tab order
- [ ] 2.10 Verify file saved

### Phase 3: Validate the Fix

- [ ] 2.11 Refresh browser at http://localhost:8098/inbox
- [ ] 2.12 Place cursor in browser address bar
- [ ] 2.13 Press Tab repeatedly to cycle through interactive elements
- [ ] 2.14 Observe that Tab now skips checkboxes and goes directly to description/category/external fields
- [ ] 2.15 Verify Approve button is still reachable via Tab
- [ ] 2.16 Record observation: "Tab now flows smoothly through editable fields, skipping checkboxes"

---

## 3. Fix: Date Chart Bar Alignment - Vega-Lite X-Axis Configuration

### Phase 1: Validate the Problem

- [ ] 3.1 Navigate to http://localhost:8098/explore
- [ ] 3.2 Scroll down to the date histogram chart (shows transaction amounts by month)
- [ ] 3.3 Take screenshot of the chart
- [ ] 3.4 Note in screenshot: bars sit BETWEEN month tick marks (not aligned with them)
- [ ] 3.5 Save screenshot as `before-chart-alignment.png`

### Phase 2: Implement the Fix

- [ ] 3.6 Open `src/pipances/routes/explore.py`
- [ ] 3.7 Find the Vega-Lite chart spec for the date histogram (search for "date_range_chart" or "x.*temporal")
- [ ] 3.8 Locate the x-axis band position configuration (likely `bandPosition: 0.5` or similar)
- [ ] 3.9 Adjust to align bars with tick marks (change to `bandPosition: 0` or adjust scale padding)
- [ ] 3.10 Verify file saved

### Phase 3: Validate the Fix

- [ ] 3.11 Refresh browser at http://localhost:8098/explore (may need server restart)
- [ ] 3.12 Scroll to the date histogram chart
- [ ] 3.13 Take screenshot of the chart
- [ ] 3.14 Note in screenshot: bars now align with month tick marks
- [ ] 3.15 Save screenshot as `after-chart-alignment.png`
- [ ] 3.16 Compare before/after screenshots to confirm alignment improved

---

## 4. Fix: Pagination Counter Styling - Remove Button Appearance

### Phase 1: Validate the Problem

- [ ] 4.1 Navigate to http://localhost:8098/inbox
- [ ] 4.2 Scroll to the bottom of the transaction table
- [ ] 4.3 Look at the pagination controls
- [ ] 4.4 Take screenshot showing the "Page X of Y" element
- [ ] 4.5 Note in screenshot: counter appears as a disabled button (gray, bordered, button-like styling)
- [ ] 4.6 Note: This looks clickable/interactive even though it's not
- [ ] 4.7 Save screenshot as `before-pagination-styling.png`

### Phase 2: Implement the Fix

- [ ] 4.8 Open `src/pipances/templates/_pagination.html`
- [ ] 4.9 Find the button with "Page {{ page }} of {{ total_pages }}" text (around line 12)
- [ ] 4.10 Replace the `<button class="btn btn-sm join-item btn-disabled">` with `<span class="text-sm">`
- [ ] 4.11 Keep the text content the same, just change tag and classes
- [ ] 4.12 Verify file saved

### Phase 3: Validate the Fix

- [ ] 4.13 Refresh browser at http://localhost:8098/inbox
- [ ] 4.14 Scroll to bottom of transaction table
- [ ] 4.15 Take screenshot showing the "Page X of Y" element
- [ ] 4.16 Note in screenshot: counter now appears as plain text (no button styling)
- [ ] 4.17 Note: It no longer looks interactive/clickable
- [ ] 4.18 Save screenshot as `after-pagination-styling.png`
- [ ] 4.19 Compare before/after screenshots to confirm styling changed

---

## 5. Fix: Pagination State After Commit - Add Out-of-Band Swap

### Phase 1: Validate the Problem

- [ ] 5.1 Navigate to http://localhost:8098/inbox
- [ ] 5.2 Select several transactions (check 3-5 checkboxes)
- [ ] 5.3 Note the current page count in pagination (e.g., "Page 1 of 2" with "50 transactions")
- [ ] 5.4 Take screenshot before committing
- [ ] 5.5 Save screenshot as `before-pagination-commit-1.png`
- [ ] 5.6 Click "Commit" button
- [ ] 5.7 Wait for response and toast notification to appear
- [ ] 5.8 Take screenshot showing the result
- [ ] 5.9 Note in screenshot: pagination counter still shows OLD values (e.g., "Page 1 of 2", original count)
- [ ] 5.10 Save screenshot as `before-pagination-commit-2.png`
- [ ] 5.11 Record observation: "Pagination doesn't update after commit; stale until page reload"

### Phase 2: Implement the Fix

- [ ] 5.12 Open `src/pipances/routes/inbox.py`
- [ ] 5.13 Find the `commit_inbox()` endpoint function
- [ ] 5.14 Locate where pagination is calculated (after querying remaining transactions)
- [ ] 5.15 When rendering `_pagination.html`, add parameter `oob=True`
- [ ] 5.16 Ensure the response includes the pagination HTML as OOB swap
- [ ] 5.17 Open `src/pipances/templates/_pagination.html`
- [ ] 5.18 Find the pagination wrapper div (first `<div>` tag in the template)
- [ ] 5.19 Add `id="inbox-pagination"` attribute if not already present
- [ ] 5.20 Add conditional attribute: `{% if oob %}hx-swap-oob="outerHTML:#inbox-pagination"{% endif %}`
- [ ] 5.21 Verify both files saved

### Phase 3: Validate the Fix

- [ ] 5.22 Refresh browser at http://localhost:8098/inbox
- [ ] 5.23 Select several transactions (check 3-5 checkboxes)
- [ ] 5.24 Note the current page count in pagination
- [ ] 5.25 Take screenshot before committing
- [ ] 5.26 Save screenshot as `after-pagination-commit-1.png`
- [ ] 5.27 Click "Commit" button
- [ ] 5.28 Wait for response and toast notification
- [ ] 5.29 Immediately take screenshot showing the result
- [ ] 5.30 Note in screenshot: pagination counter now shows UPDATED values (new page count, updated transaction count)
- [ ] 5.31 Save screenshot as `after-pagination-commit-2.png`
- [ ] 5.32 Compare before/after screenshots to confirm pagination updates in-place after commit
- [ ] 5.33 Verify row count decreased (committed transactions removed from inbox)

---

## 6. Code Quality and Final Verification

- [ ] 6.1 Run `just fmt` to auto-format Python and templates
- [ ] 6.2 Run `just lint` to check for linting errors
- [ ] 6.3 Compile all before/after screenshots into a comparison document
- [ ] 6.4 Review each fix one more time in browser to ensure no regressions
- [ ] 6.5 Test all 5 fixes together in a single inbox/import session
- [ ] 6.6 Verify no conflicts between fixes
