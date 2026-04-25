## Why

The combobox component has multiple interrelated bugs: the dropdown gets clipped by parent containers (modals, overflow), doesn't dismiss on click-off reliably, has no Enter behavior for submitting typed text, can't flip above the input when near the bottom of the viewport, and visually looks out-of-place compared to DaisyUI-styled components. These issues compound into a frustrating editing experience for the primary transaction review workflow.

The HTML Popover API (Baseline 2024, supported in all modern browsers) combined with CSS Anchor Positioning solves the layering and positioning problems natively, without z-index hacks or JS positioning libraries. DaisyUI v5 already documents this pattern for its dropdown component.

## What Changes

- Replace `absolute` + `z-50` dropdown positioning with the **HTML Popover API** (`popover="manual"`) and **CSS Anchor Positioning** (`anchor-name`, `position-anchor`, `position-try-fallbacks: flip-block`)
- The dropdown renders in the browser's **top layer**, escaping all stacking contexts (modals, overflow containers)
- The dropdown **auto-flips above** the input when there's insufficient space below
- Clicking outside the dropdown **dismisses it** via native popover light-dismiss behavior (managed via JS since we use `popover="manual"` for HTMX control)
- Restyle the input to use DaisyUI's `input input-bordered` class instead of custom transparent/borderless styling
- Restyle the results list to use DaisyUI's `menu` component with proper `<li>` items and hover/active states
- Fix Enter key behavior: Enter with nothing highlighted does nothing when selectable items exist; Enter creates a new entry only when "+ Create" is the sole option
- Clean up the inline JS IIFE for clarity: separate open/close, highlight, and submit concerns

## Capabilities

### New Capabilities

_(none — this is a rewrite of existing capability)_

### Modified Capabilities

- `combo-box`: The "Enter with no highlight" behavior changes — Enter now only auto-creates when the Create option is the sole item in the dropdown. Previously, Enter with an exact case-insensitive match would select it; now Enter with no highlight always does nothing if there are selectable items present. Additionally, dropdown positioning, layering, dismiss-on-click-off, and visual styling are improved (implementation details, but the clipping fix is already a stated requirement).

## Impact

- **Templates**: `shared/_combo_edit.html` (complete rewrite), `shared/_combo_results.html` (restyle to DaisyUI menu items)
- **CSS**: New anchor positioning styles (may need a small `<style>` block or additions to `input.css`)
- **JS**: Rewritten inline IIFE in `_combo_edit.html` — same responsibilities but using `showPopover()`/`hidePopover()` instead of display toggling
- **Backend**: No changes to `routes/widgets.py` or the combo search endpoint
- **Browser support**: Popover API is Baseline 2024 (Chrome 114+, Firefox 125+, Safari 17+). CSS Anchor Positioning is Chrome 125+ and Firefox 131+. Safari fallback may need a polyfill or absolute-positioning fallback.
