## 0. UI Test Scaffolding (write first, must fail before implementing)

- [x] 0.1 Create `tests/ui/test_combobox_popover.py` with Playwright tests for the modified combo-box spec scenarios:
  - Dropdown not clipped by modal (popover visible above dialog)
  - Dropdown flips above when near bottom of viewport
  - Enter with no highlight and selectable items present → no action, dropdown stays open
  - Enter with no highlight and only Create option → creates the entity
  - Blur without selection → dropdown closes, value reverts
  - Click on dropdown item does not trigger blur (item is applied)
- [x] 0.2 Run `just test-ui` and confirm all new tests FAIL

## 1. Popover API dropdown structure

- [x] 1.1 Rewrite `_combo_edit.html`: replace the `<div class="combo-box relative">` wrapper with a structure using `popover="manual"` on the results container. Add `anchor-name` CSS on the input and `position-anchor` + `position-try-fallbacks: flip-block` on the popover element.
- [x] 1.2 Add a `@supports not (anchor-name: --x)` CSS fallback block for Safari that positions the dropdown with `position: absolute; top: 100%` (no flip, but functional).
- [x] 1.3 Restyle the input from `bg-transparent p-0 border-0 border-b` to DaisyUI `input input-bordered w-full`.

## 2. DaisyUI menu results list

- [x] 2.1 Rewrite `_combo_results.html`: replace `<div data-combo-item>` elements with `<ul class="menu ..."><li><button>` structure using DaisyUI menu classes. Add `tabindex="-1"` to items so they can be `relatedTarget` for focusout.
- [x] 2.2 Style the highlighted item using DaisyUI's `active` class instead of manually toggling `bg-primary text-primary-content`.
- [x] 2.3 Style the "+ Create" option as a visually distinct menu item (border-top separator, success-colored text, plus icon).

## 3. JS IIFE rewrite

- [x] 3.1 Replace popover show/hide logic: use `el.showPopover()` / `el.hidePopover()` driven by `htmx:afterSwap` events on the results container. Show when results are non-empty, hide when empty.
- [x] 3.2 Replace blur handling: use `focusout` on the wrapper with `relatedTarget` check. If `relatedTarget` is inside the popover, don't dismiss. Otherwise, revert and hide popover.
- [x] 3.3 Update Enter key behavior: if `highlightIndex === -1`, check if the only item in the dropdown is a Create option. If so, click it. Otherwise, do nothing (don't close, don't submit).
- [x] 3.4 Keep existing arrow key navigation and MutationObserver highlight reset. Update highlight styling to toggle the DaisyUI `active` class.
- [x] 3.5 Add click-outside dismiss: listen for `click` on `document` when popover is open; if click target is outside the wrapper and popover, hide popover and revert.

## 4. Integration and build

- [x] 4.1 Run `just css` to rebuild Tailwind CSS with any new DaisyUI classes used.
- [x] 4.2 Verify the modal edit flow works end-to-end: open modal → click into Description → type → see popover dropdown → select item → field updates. Repeat for External Account and Category.
- [x] 4.3 Test the popover inside the modal visually: confirm the dropdown is not clipped and sits above the dialog backdrop.

## 5. Verification

- [x] 5.1 Run `just test-ui` and confirm all tests from step 0 now PASS
- [x] 5.2 Run `just test` to confirm no unit test regressions
- [x] 5.3 Run `just fmt` and `just lint` to verify code quality
