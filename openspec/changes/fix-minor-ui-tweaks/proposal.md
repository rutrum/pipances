## Why

Five small UI inconsistencies and quality-of-life issues impact daily usability: keyboard navigation skips unexpectedly, controls look disabled when they're not, visual alignment is off in charts, and state doesn't update properly after bulk actions. These are quick wins that improve polish and reduce friction.

## What Changes

1. **Account dropdown vertical centering** — Fix vertical alignment of the `<select>` element in the manual transaction entry form
2. **Tab navigation skips checkboxes** — Add `tabindex="-1"` to row selection checkboxes so keyboard users can tab through editable fields without getting stuck on checkboxes
3. **Date chart bar alignment** — Adjust Vega-Lite x-axis configuration in the Explore page so histogram bars align with month tick marks
4. **Pagination counter styling** — Change the "Page X of Y" element from a disabled button to unstyled text (no longer looks disabled, no longer suggests clickability)
5. **Pagination updates after commit** — Add out-of-band swap for pagination element after committing transactions so row count and page numbers refresh correctly

## Capabilities

### New Capabilities
<!-- None - these are refinements to existing functionality, not new features -->

### Modified Capabilities
<!-- These fixes don't change user-facing requirements, only implementation quality -->
<!-- No specs need delta updates; this is a pure implementation pass -->

## Impact

- **Templates affected**: `_import_manual.html`, `_inbox_row.html`, `_pagination.html`, `explore.html`
- **Routes affected**: `inbox.py` (commit endpoint), `explore.py` (chart generation)
- **CSS/styling**: Minor DaisyUI class adjustments
- **JavaScript**: Minimal (tabindex attribute, no behavior changes)
- **Database**: None
- **Dependencies**: None
- **Breaking changes**: None
