## Context

The combobox component (`_combo_edit.html` + `_combo_results.html`) is used exclusively inside the transaction edit modal for Description, External Account, and Category fields. The modal is a `<dialog>` element.

The current dropdown uses `position: absolute` + `z-index: 50` inside the modal. This creates two fundamental problems:
1. The dropdown is confined to the modal's stacking context and gets clipped by `overflow` rules
2. There's no positioning logic to flip above the input when near the viewport bottom

The input is styled with raw Tailwind (`bg-transparent p-0 border-0 border-b`) and the results use custom `px-3 py-2 hover:bg-base-200` styling rather than DaisyUI components.

The blur/dismiss logic uses a fragile `setTimeout(200ms)` + `preventBlurRevert` flag pattern that races with click events on dropdown items.

## Goals / Non-Goals

**Goals:**
- Dropdown renders above all other elements (including `<dialog>` modals) using the Popover API top layer
- Dropdown auto-flips above the input when insufficient space below
- Clicking outside reliably dismisses the dropdown
- Input and results list use DaisyUI component classes (`input`, `menu`) for visual consistency
- Enter key behavior is well-defined per the updated spec
- JS is cleaner and less race-prone

**Non-Goals:**
- Fuzzy search / relevancy sorting (tracked in beads: pipances-ec7)
- Filtering unapproved external accounts (tracked in beads: pipances-0u0)
- ML prediction display with confidence scores (tracked in beads: pipances-jwa)
- Making the dropdown wider than the input (tracked in beads: pipances-yi1)
- ARIA combobox role attributes (good idea but separate change)
- Changing the backend `/api/combo/{entity}` endpoint

## Decisions

### 1. Popover API with `popover="manual"` (not `popover="auto"`)

**Choice**: Use `popover="manual"` controlled by JS, not `popover="auto"`.

**Why**: `popover="auto"` provides light-dismiss for free, but it has a critical conflict — showing an `auto` popover closes other `auto` popovers. Since the combobox lives inside a `<dialog>` (which is also in the top layer), and because we need fine-grained control over when the popover opens/closes (driven by HTMX result swaps, not clicks), `manual` is safer. We handle dismiss ourselves on blur/escape/outside-click.

**Alternative rejected**: `popover="auto"` — simpler but risks interfering with the dialog and loses control over show/hide timing tied to HTMX responses.

### 2. CSS Anchor Positioning with fallback

**Choice**: Use CSS `anchor-name` / `position-anchor` / `position-try-fallbacks: flip-block` for positioning. Include an absolute-positioning fallback for Safari (which doesn't yet support anchor positioning).

**Why**: CSS anchor positioning is the native solution for tethering a popover to its trigger element. It handles flip-above automatically. The fallback ensures the combobox still works in Safari (it just won't auto-flip; it'll default to below).

**Approach**: 
- Primary: `anchor-name: --combo-anchor-{id}` on the input, matched by `position-anchor` on the popover
- Fallback: `@supports not (anchor-name: --x)` block with `position: absolute; bottom: 100%` or `top: 100%`

### 3. DaisyUI `menu` for results list

**Choice**: Use `<ul class="menu bg-base-200 rounded-box shadow-xl">` with `<li><button>` items.

**Why**: DaisyUI's `menu` component provides hover, focus, and active states out of the box. The current custom `div` items with `hover:bg-base-200` don't match the rest of the UI. Menu items also get proper padding, border-radius, and transition effects.

### 4. DaisyUI `input input-bordered` for the text field

**Choice**: Replace the custom `bg-transparent border-b` input with `input input-bordered w-full`.

**Why**: Consistency with every other form input in the app. The "ghost" styling was an artifact of when the combobox was inline in table cells; in the modal context, a proper bordered input is more appropriate and discoverable.

### 5. Dismiss-on-click-off via `focusout` + event delegation

**Choice**: Replace the `blur` + `setTimeout(200ms)` + `preventBlurRevert` pattern with a single `focusout` handler on the wrapper that checks `relatedTarget`. If `relatedTarget` is inside the popover, don't dismiss. Otherwise, dismiss.

**Why**: The current approach has race conditions where the 200ms timeout either fires too early (dismissing before the click registers) or the `preventBlurRevert` flag gets stuck. `focusout` + `relatedTarget` is the standard pattern and doesn't need timers.

**Detail**: Popover items need `tabindex="-1"` so they can receive focus and appear as `relatedTarget`.

### 6. Show/hide popover driven by HTMX swap events

**Choice**: Show the popover when HTMX swaps content into the results container (via `htmx:afterSwap` event). Hide it when results are empty or on dismiss.

**Why**: The popover should only be visible when there are results to show. Tying visibility to the HTMX response lifecycle (rather than input events) ensures the popover appears precisely when content is ready.

## Risks / Trade-offs

- **[Safari anchor positioning]** → Safari doesn't support CSS Anchor Positioning yet. Mitigation: absolute-positioning fallback. The dropdown will work but won't auto-flip above. Since this is a self-hosted app, the user can use Chrome/Firefox.
- **[Popover API + HTMX interaction]** → HTMX swaps content into the popover element; we need to ensure the popover stays shown during content updates. Mitigation: use `htmx:beforeSwap` / `htmx:afterSwap` listeners to manage popover state around swaps.
- **[Dialog + popover stacking]** → Both `<dialog>` and `popover` elements live in the top layer. The later one opened should stack on top. Since the combobox popover opens after the dialog, this should work. Mitigation: test explicitly.
