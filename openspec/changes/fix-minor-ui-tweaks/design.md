## Context

The codebase uses Tailwind CSS + DaisyUI for styling and Vega-Lite for charting. Template rendering is done server-side with Jinja2. Transaction inbox uses HTMX for interactions with out-of-band (OOB) swaps for multi-element updates.

Currently, five small issues create minor friction:
1. The account `<select>` in manual entry doesn't center vertically relative to its label
2. Row checkboxes receive focus during keyboard navigation, forcing users to press Tab multiple times
3. Histogram bars in the Explore page sit between tick marks instead of aligned with them
4. The pagination counter appears as a disabled button, suggesting it's not interactive
5. After committing transactions, pagination still shows the old row count and page totals

## Goals / Non-Goals

**Goals:**
- Fix all five issues with minimal code changes
- Maintain 100% behavioral equivalence (no feature changes)
- Keep implementation simple (CSS/template adjustments, no new abstractions)
- Verify each fix works via browser testing

**Non-Goals:**
- Redesign the pagination component
- Refactor chart generation architecture
- Add new interaction patterns
- Change how OOB swaps work globally

## Decisions

### Decision 1: Vertical Centering via CSS Class Adjustment

**Chosen:** Add `items-center` flex container class to the form-control parent or adjust select wrapper styling.

**Rationale:**
- DaisyUI `form-control` uses flexbox; `items-center` vertically centers children
- Single-line change; no behavioral impact
- Matches existing Tailwind patterns in the codebase

---

### Decision 2: Tab Navigation via `tabindex="-1"` on Checkboxes

**Chosen:** Add `tabindex="-1"` attribute to checkbox inputs in `_inbox_row.html`.

**Rationale:**
- `tabindex="-1"` removes element from tab order entirely; Tab key skips over it
- Checkboxes are redundant with "Approve" button; they're secondary controls
- No JavaScript needed; pure HTML attribute
- Standard accessibility pattern for subordinate controls

---

### Decision 3: Chart Bar Alignment via Vega-Lite X-Axis Config

**Chosen:** Adjust Vega-Lite x-axis `bandPosition` or offset to align bars with tick marks (not between them).

**Rationale:**
- Vega-Lite encodes data on x-axis; current config likely has `bandPosition: 0.5` (bar center on tick)
- Change to `bandPosition: 0` or adjust padding to shift bars left
- Only affects the chart spec in `explore.py`; no template changes

---

### Decision 4: Pagination Counter as Plain Text

**Chosen:** Change from `<button class="btn btn-sm join-item btn-disabled">` to `<span class="text-sm">` or similar neutral text styling.

**Rationale:**
- Current button styling makes users think it's clickable; it's not
- Span with text-sm matches the "X transactions" label styling on the right
- Removes visual lie without changing functionality

---

### Decision 5: Pagination OOB Swap After Commit

**Chosen:** When committing transactions in `inbox.py`, include an out-of-band response that swaps the pagination HTML fragment.

**Rationale:**
- Currently, commit returns row HTML but doesn't update pagination
- Pagination shows stale counts until page reload
- Using OOB swap keeps the two updates in a single response
- Add `id="inbox-pagination"` to pagination wrapper and render with `hx-swap-oob="outerHTML:#inbox-pagination"` attribute

**Pattern:**
```python
# In inbox.py commit_inbox():
pagination_fragment = render_template("_pagination.html", {
    "page": 1,
    "total_pages": total_pages,
    "total_count": remaining_count,
    "pagination_url": "/inbox",
    "oob": True,  # Flag to include hx-swap-oob attribute
})

# Return rows + pagination OOB + toast
return HTMLResponse(rows_html + pagination_fragment + toast_html)
```

**Template change (_pagination.html):**
```html
<div id="inbox-pagination"
     {% if oob %}hx-swap-oob="outerHTML:#inbox-pagination"{% endif %}
     class="flex items-center justify-between mt-4">
  <!-- pagination content -->
</div>
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Tabindex change affects keyboard-only users negatively** | Actually improves UX; users can now reach all editable fields without extra tabs. Checkboxes redundant with Approve button. |
| **Vega-Lite config change breaks other charts** | Only affects date histogram in Explore; other charts use different specs. Verify via screenshot. |
| **OOB swap doesn't render (silent failure)** | Test in browser after commit; verify pagination updates. Add console check if swap doesn't fire. |
| **Centered dropdown breaks on mobile/small screens** | Tailwind `items-center` responsive-safe; test on mobile viewport. |

## Migration Plan

**Approach:** Roll out each fix independently; verify after each.

1. **Fix 1 (dropdown centering)**: Edit `_import_manual.html`, test in browser
2. **Fix 2 (tabindex)**: Edit `_inbox_row.html`, test Tab key through row
3. **Fix 3 (chart alignment)**: Edit `explore.py` Vega spec, take screenshot comparison
4. **Fix 4 (pagination styling)**: Edit `_pagination.html`, verify appearance
5. **Fix 5 (pagination OOB)**: Edit `_pagination.html` (add oob flag) + `inbox.py` (commit endpoint), test commit flow

**Rollback:** Each fix is isolated; revert just the affected file if an issue arises.

## Open Questions

None. All fixes are straightforward and scoped.
