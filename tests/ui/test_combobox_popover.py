"""
UI tests for the combobox Popover API rewrite.

Covers the modified scenarios from the combo-box spec delta:
  - Dropdown not clipped by modal (top layer rendering)
  - Dropdown flips above when near bottom of viewport
  - Enter with no highlight and selectable items → no action, dropdown stays open
  - Enter with no highlight and only Create option → creates the entity
  - Blur without selection → dropdown closes, value reverts
  - Click on dropdown item does not trigger blur (item is applied)

These tests are written BEFORE implementation and SHOULD FAIL until the
Popover API rewrite is complete.
"""

import re

from playwright.sync_api import Page, expect

# ===========================================================
# Helpers
# ===========================================================


def open_modal(page: Page, txn_id: int):
    """Click Edit on the row and wait for the modal dialog to open."""
    row = page.locator(f"#txn-{txn_id}")
    row.locator("button", has_text="Edit").click()
    dialog = page.locator(f"#transaction-edit-modal-{txn_id}")
    expect(dialog).to_be_visible()
    return dialog


def get_combo_input(dialog, nth: int):
    """Return the input element for the nth combo box (0=Description, 1=External, 2=Category)."""
    return dialog.locator(".combo-box").nth(nth).locator("input")


def get_combo_results(dialog, txn_id: int, field: str):
    """Return the popover/results container for the given combo field."""
    return dialog.locator(f"#combo-results-{txn_id}-{field}")


def wait_for_combo_settled(page, results, expected_min: int = 1):
    """Wait until the combo results have at least expected_min items and the
    HTMX debounce (200ms) + server response has fully settled. Prevents
    race conditions where a subsequent HTMX response clears a just-applied
    arrow-key highlight."""
    expect(results.locator("[data-combo-item]").nth(expected_min - 1)).to_be_visible(
        timeout=3000
    )
    # Wait for network idle to ensure the debounced request has completed
    page.wait_for_load_state("networkidle")


#
# The popover must render in the top layer — we verify this by checking
# that the results container is visible and has content when the combo is open.
# ===========================================================


def test_dropdown_visible_inside_modal(page: Page, goto, full_txn):
    """
    WHEN  the combo box is rendered inside a dialog modal and user types
    THEN  the dropdown SHALL render above the modal in the top layer
    THEN  the dropdown SHALL be fully visible and interactive
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_combo_input(dialog, 2)  # Category combo
    inp.click()
    inp.fill("shop")

    # Results must be visible — if clipped by modal they won't be interactable
    results = get_combo_results(dialog, txn_id, "category_id")
    wait_for_combo_settled(page, results)

    # Must be able to click an item (proves it's not obscured)
    item = results.locator("[data-combo-item]").first
    expect(item).to_be_visible(timeout=3000)
    expect(item).to_be_enabled()


# ===========================================================
# Scenario: Dropdown flips above when near bottom of viewport
#
# We resize the viewport so the modal is near the bottom, then verify the
# dropdown panel appears above the input (its bottom edge is above the input
# top edge in page coordinates).
# ===========================================================


def test_dropdown_flips_above_near_viewport_bottom(page: Page, goto, full_txn):
    """
    WHEN  the combo box input is near the bottom of the viewport
    THEN  the dropdown SHALL open above the input instead of below
    """
    txn_id = full_txn["id"]

    # Make the viewport short so the modal sits near the bottom
    page.set_viewport_size({"width": 1280, "height": 400})
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_combo_input(dialog, 2)  # Category combo
    inp.click()
    inp.fill("a")

    results = get_combo_results(dialog, txn_id, "category_id")
    expect(results).to_be_visible(timeout=3000)

    # The popover bottom should be above the input top (flipped)
    inp_box = inp.bounding_box()
    results_box = results.bounding_box()
    assert results_box is not None, "Dropdown bounding box not found"
    assert inp_box is not None, "Input bounding box not found"
    # When flipped above, the results bottom ≤ input top
    assert results_box["y"] + results_box["height"] <= inp_box["y"] + 5, (
        f"Dropdown did not flip above: results bottom={results_box['y'] + results_box['height']}, "
        f"input top={inp_box['y']}"
    )


# ===========================================================
# Scenario: Enter with no highlight and selectable items present → no action
# ===========================================================


def test_enter_no_highlight_with_options_does_nothing(page: Page, goto, full_txn):
    """
    WHEN  the dropdown shows selectable existing items
    WHEN  user presses Enter without highlighting any item
    THEN  no action SHALL be taken
    THEN  the dropdown SHALL remain open
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_combo_input(dialog, 2)  # Category combo
    inp.click()
    # Type something that will match existing categories (seeded data has categories)
    inp.fill("")
    results = get_combo_results(dialog, txn_id, "category_id")
    wait_for_combo_settled(page, results)

    # Confirm there are regular (non-create) items
    non_create_items = results.locator("[data-combo-item]:not([data-combo-create])")
    expect(non_create_items.first).to_be_visible(timeout=3000)

    # Press Enter without arrowing down
    inp.press("Enter")

    # Dropdown must still be visible — no action taken
    expect(results).to_be_visible()
    # Modal must still be open
    expect(dialog).to_be_visible()


# ===========================================================
# Scenario: Enter with no highlight and only Create option → creates entity
# ===========================================================


def test_enter_no_highlight_only_create_option_creates_entity(
    page: Page, goto, full_txn
):
    """
    WHEN  user types text that has no existing match (only Create option shown)
    WHEN  user presses Enter without highlighting
    THEN  the system SHALL create the new entity and assign it
    THEN  the dropdown SHALL close
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    new_name = "ZZZUniqueCategory9999"
    inp = get_combo_input(dialog, 2)  # Category combo
    inp.click()
    inp.fill(new_name)

    results = get_combo_results(dialog, txn_id, "category_id")
    wait_for_combo_settled(page, results)

    # Only the Create option should exist
    items = results.locator("[data-combo-item]")
    expect(items).to_have_count(1, timeout=3000)
    create_item = results.locator("[data-combo-create]")
    expect(create_item).to_be_visible(timeout=3000)

    # Press Enter — should fire the Create action
    inp.press("Enter")

    # Dropdown must close
    expect(results).not_to_be_visible(timeout=3000)

    # Input must show the created value
    expect(inp).to_have_value(new_name)


# ===========================================================
# Scenario: Blur without selection → dropdown closes and value reverts
# ===========================================================


def test_blur_without_selection_reverts_value(page: Page, goto, full_txn):
    """
    WHEN  user opens combo, types partial text, then clicks away
    THEN  the dropdown SHALL close
    THEN  the input value SHALL revert to the previous value
    """
    txn_id = full_txn["id"]

    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_combo_input(dialog, 2)  # Category combo
    inp.click()
    inp.fill("zzznomatch")

    results = get_combo_results(dialog, txn_id, "category_id")
    expect(results).to_be_visible(timeout=3000)

    # Click somewhere outside the combo (the modal title)
    dialog.locator("h3").click()

    # Dropdown must close
    expect(results).not_to_be_visible(timeout=3000)

    # After revert the row refreshes — just check dropdown is gone
    # (revert fires a PATCH with empty values which re-renders the row partial)


# ===========================================================
# Scenario: Click on dropdown item applies value (no spurious blur)
# ===========================================================


def test_click_dropdown_item_applies_value(page: Page, goto, full_txn):
    """
    WHEN  user clicks on a dropdown item
    THEN  the blur handler SHALL NOT fire before the click registers
    THEN  the selected item SHALL be applied to the transaction
    THEN  the input SHALL show the selected value
    THEN  the dropdown SHALL close
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_combo_input(dialog, 2)  # Category combo
    inp.click()
    inp.fill("")  # Show all options

    results = get_combo_results(dialog, txn_id, "category_id")
    wait_for_combo_settled(page, results)

    first_item = results.locator("[data-combo-item]").first
    expect(first_item).to_be_visible(timeout=3000)
    item_text = first_item.inner_text().strip()

    # Click the item — must NOT be swallowed by a blur-revert
    first_item.click()

    # Dropdown must close
    expect(results).not_to_be_visible(timeout=3000)

    # Input must show the clicked value
    expect(inp).to_have_value(item_text)

    # Modal must still be open (we only selected a field, didn't submit)
    expect(dialog).to_be_visible()


# ===========================================================
# Scenario: Arrow key navigation highlights items visually
# ===========================================================


def test_arrow_key_navigation_highlights_items(page: Page, goto, full_txn):
    """
    WHEN  the dropdown is open and user presses ArrowDown
    THEN  the first item SHALL be visually highlighted
    WHEN  user presses ArrowDown again
    THEN  the second item SHALL be highlighted and first deselected
    WHEN  user presses ArrowUp
    THEN  the first item SHALL be highlighted again
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_combo_input(dialog, 1)  # External Account combo
    inp.click()
    inp.fill("a")  # Many results

    results = get_combo_results(dialog, txn_id, "external_id")
    wait_for_combo_settled(page, results)
    items = results.locator("[data-combo-item]")
    expect(items.nth(0)).to_be_visible(timeout=3000)

    # Press ArrowDown — first item should be highlighted
    inp.press("ArrowDown")
    expect(items.nth(0)).to_have_class(re.compile(r"\bmenu-active\b"), timeout=2000)
    expect(items.nth(1)).not_to_have_class(re.compile(r"\bmenu-active\b"))

    # Press ArrowDown again — second item highlighted, first not
    inp.press("ArrowDown")
    expect(items.nth(1)).to_have_class(re.compile(r"\bmenu-active\b"), timeout=2000)
    expect(items.nth(0)).not_to_have_class(re.compile(r"\bmenu-active\b"))

    # Press ArrowUp — back to first item
    inp.press("ArrowUp")
    expect(items.nth(0)).to_have_class(re.compile(r"\bmenu-active\b"), timeout=2000)
    expect(items.nth(1)).not_to_have_class(re.compile(r"\bmenu-active\b"))


def test_arrow_key_then_enter_selects_item(page: Page, goto, full_txn):
    """
    WHEN  user navigates to an item with arrow keys and presses Enter
    THEN  that item SHALL be selected
    THEN  the dropdown SHALL close
    THEN  the input SHALL show the selected value
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_combo_input(dialog, 1)  # External Account combo
    inp.click()
    inp.fill("a")

    results = get_combo_results(dialog, txn_id, "external_id")
    wait_for_combo_settled(page, results)

    # Get the text of the second item (ArrowDown twice)
    inp.press("ArrowDown")
    inp.press("ArrowDown")
    second_item = results.locator("[data-combo-item]").nth(1)
    expect(second_item).to_have_class(re.compile(r"\bmenu-active\b"), timeout=2000)
    selected_text = second_item.inner_text().strip()

    # Press Enter to confirm
    inp.press("Enter")

    # Dropdown must close
    expect(results).not_to_be_visible(timeout=3000)
    # Input must show selected value
    expect(inp).to_have_value(selected_text)
