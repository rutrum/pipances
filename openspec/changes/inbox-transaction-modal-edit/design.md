## Context

Currently, inbox transactions are edited via three inline click-to-edit fields embedded in the table row. Each field (description, external, category) triggers a separate GET request to load a combo-box or input, and changes are persisted immediately. This approach works but is scattered and difficult to maintain as a cohesive form.

The goal is to move to a modal-based form for editing individual transactions, centralizing all edit logic while maintaining immediate field persistence and reducing template complexity.

**Current flow:**
- User clicks on one of three inline editable fields
- HTMX GET fetches field-specific edit template (3 different endpoints)
- User types/selects, change persists on blur/change
- User closes via escape or clicking elsewhere
- Row remains visible (no explicit refresh)

**Key constraint:** All changes must persist immediately (field-by-field), not deferred until a form submit.

## Goals / Non-Goals

**Goals:**
- Provide a single, cohesive form for editing all three transaction fields (description, external, category)
- Maintain immediate field persistence (no "Apply" button for individual records)
- Display full transaction context (date, raw description, amount) in modal
- Simplify row template: remove click-to-edit logic, make it display-only
- Reduce endpoint complexity: consolidate three inline-edit endpoints into one modal endpoint
- Enable future extensibility (modal can easily accommodate new fields like ML confidence data)
- Use DaisyUI modal for consistent styling

**Non-Goals:**
- Bulk editing modal (separate future work tracked in beads)
- Validation preventing field save (only blocks approval)
- Keyboard shortcuts or advanced form interactions
- Transaction duplication or archival features
- ML prediction UI (reserved for future enhancement)

## Decisions

### Decision 1: Modal Interaction Pattern
**Choice:** Use DaisyUI's `<dialog>` element with HTMX for opening.
- **Rationale:** DaisyUI provides consistent styling and semantic HTML. HTMX can trigger the GET for modal content and return HTML that JavaScript then displays in the dialog.
- **Alternative considered:** Pure HTMX dialog extension — would require external dependency and adds coupling to HTMX internals.
- **Implementation:** 
  - Edit button: `hx-get="/transactions/{id}/edit-modal"` returns modal HTML
  - Simple inline JS: `<dialog>.showModal()` after HTMX swap
  - Close via `<button type="button" onclick="this.closest('dialog').close()">X</button>`

### Decision 2: Field Persistence Timing
**Choice:** Each field persists immediately on blur (text input) or change (selects). No staging.
- **Rationale:** User already expects this from current inline editing. Immediate feedback is critical for trust. Users can always refresh or re-edit if needed.
- **Implementation:** Each input/select carries HTMX attributes: `hx-trigger="blur"` or `hx-trigger="change"` → PATCH `/transactions/{id}` with just that field.

### Decision 3: Row Refresh After Modal Close
**Choice:** Fire a silent GET to refresh the row when modal closes.
- **Rationale:** Decouples modal lifecycle from row update. Clean separation: modal returns its own updated form (for error feedback), then we fetch fresh row data.
- **Implementation:**
  - On modal close (JS handler on `<dialog close>` event)
  - Fire HTMX GET `/transactions/{id}/row` (returns just the `<tr>` HTML)
  - Replace existing row via HTMX OOB swap or direct DOM update

### Decision 4: Error Handling
**Choice:** Field-level errors display inline in modal (next to the field), modal stays open.
- **Rationale:** User can immediately see what went wrong and retry without losing context.
- **Implementation:** PATCH endpoint returns 422 with error response; template includes error div that HTMX targets.

### Decision 5: Reuse Existing Combo-Box Component for External & Category
**Choice:** Reuse existing `_combo_edit.html` component for external account and category fields in the modal.
- **Rationale:** 
  - Combo-box features (search, filtering, inline creation) are critical UX requirements
  - Modal provides better space than table cells for dropdown overflow and keyboard navigation
  - Existing implementation already handles: autocomplete, arrow key navigation, Escape to cancel, Enter to select
  - Maintains consistency with current inline editing behavior
- **Challenges & mitigation:**
  - Dropdown positioning: Modal context needs z-index handling. Combo-box uses `absolute z-50` which should work in modal.
  - Focus management: Modal auto-closes on Escape; need to prevent that if user is navigating combo-box results. Solution: Detect if combo-box dropdown is visible before allowing modal close.
- **Implementation:**
  - Description: Text input with `hx-trigger="blur"` (simple, no search needed)
  - External account: Reuse `_combo_edit.html` with field_name="external_id"
  - Category: Reuse `_combo_edit.html` with field_name="category_id"
  - Both combo-boxes trigger PATCH on selection via existing mechanism

### Decision 6: Endpoint Consolidation
**Choice:** Remove `/transactions/{id}/edit-description-combo`, `/edit-external`, `/edit-category` endpoints.
- **Rationale:** All three are now handled by one modal endpoint + one PATCH endpoint. Simpler codebase, easier to reason about.
- **Implementation:**
  - GET `/transactions/{id}/edit-modal` returns complete modal form
  - PATCH `/transactions/{id}` (existing) handles field updates from both inline and modal

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Lost inline edit muscle memory** | Inline editing (blur-to-save) was faster for power users. Modal adds a click. Accepted: form UX gains outweigh this. |
| **Extra GET for row refresh** | After modal closes, we fetch the row again. One extra request. Accepted: clean separation of concerns. Consider caching row data in JS if this becomes slow. |
| **Dialog not supported on older browsers** | DaisyUI's dialog component degrades gracefully. Acceptable for internal tools. |
| **Field-level PATCH requests** | Three fields = potentially three PATCH calls if user edits all three. Acceptable: DB latency minimal, feedback immediate. |

## Migration Plan

1. **New code, old coexists:** Add new modal templates and endpoint alongside existing inline-edit endpoints (no breaking change yet).
2. **Redirect traffic:** Update inbox row to use new Edit button instead of inline clicks. Old endpoints remain but unused.
3. **Remove old endpoints:** Once confirmed working, delete three old edit endpoints + their templates + related routes.
4. **Test:** Verify modal field updates, row refresh, error cases, modal close behavior.

## Open Questions

- Should the modal auto-focus the first field (description) when opened?
- If description field is blank, should the modal show a warning, or only prevent approval?
- Should ML confidence badges appear in the modal? (Punt to future: can add in next iteration)
