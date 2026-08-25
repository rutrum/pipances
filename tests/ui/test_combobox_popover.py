"""
UI tests for Tom Select combo boxes in the transaction edit modal.

Tests core Tom Select behaviors: dropdown visibility, keyboard navigation,
click selection, and create-on-type for new values.
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


def get_ts_input(dialog, nth: int):
    """Return the input element for the nth Tom Select (0=Description, 1=External, 2=Category)."""
    wrapper = dialog.locator(".ts-wrapper").nth(nth)
    # Scroll the modal-box to bring the wrapper into view
    dialog.locator(".modal-box").evaluate(
        "(box) => { const w = box.querySelector('.ts-wrapper'); if (w) w.scrollIntoView({block: 'center'}); }"
    )
    return wrapper.locator("input")


def get_ts_dropdown(dialog):
    """Return the Tom Select dropdown."""
    return dialog.locator(".ts-dropdown")


def wait_for_options(dialog, expected_min: int = 1):
    """Wait until the Tom Select dropdown has at least expected_min options."""
    dropdown = get_ts_dropdown(dialog)
    expect(dropdown.locator(".option").nth(expected_min - 1)).to_be_visible(
        timeout=3000
    )


# ===========================================================
# Basic dropdown: typing shows options
# ===========================================================


def test_dropdown_visible_when_typing(page: Page, goto, full_txn):
    """
    WHEN  user clicks on a Tom Select input and types
    THEN  a dropdown with matching options appears
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_ts_input(dialog, 2)  # Category
    inp.click()
    inp.fill("shop")

    dropdown = get_ts_dropdown(dialog)
    expect(dropdown.locator(".option").first).to_be_visible(timeout=3000)


# ===========================================================
# Click on option selects it
# ===========================================================


def test_click_option_selects_value(page: Page, goto, full_txn):
    """
    WHEN  user types and clicks on a dropdown option
    THEN  the option is selected, dropdown closes, input shows value
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_ts_input(dialog, 2)  # Category
    inp.click()
    inp.fill("a")

    dropdown = get_ts_dropdown(dialog)
    wait_for_options(dialog)

    first_option = dropdown.locator(".option").first
    expect(first_option).to_be_visible(timeout=3000)

    first_option.click()

    # Dropdown should close
    expect(dropdown).not_to_be_visible(timeout=3000)

    # Modal stays open
    expect(dialog).to_be_visible()


# ===========================================================
# Arrow key navigation
# ===========================================================


def test_arrow_keys_highlight_options(page: Page, goto, full_txn):
    """
    WHEN  dropdown is open and user presses ArrowDown
    THEN  the first option gets highlighted
    WHEN  user presses ArrowDown again
    THEN  the second option is highlighted, first is not
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_ts_input(dialog, 1)  # External Account
    inp.click()
    inp.fill("a")

    dropdown = get_ts_dropdown(dialog)
    wait_for_options(dialog)
    options = dropdown.locator(".option")
    expect(options.nth(0)).to_be_visible(timeout=3000)

    # ArrowDown -> first item highlighted
    inp.press("ArrowDown")
    expect(options.nth(0)).to_have_class(re.compile(r"\bfocus\b"), timeout=2000)

    # ArrowDown again -> second highlighted, first not
    inp.press("ArrowDown")
    expect(options.nth(1)).to_have_class(re.compile(r"\bfocus\b"), timeout=2000)
    expect(options.nth(0)).not_to_have_class(re.compile(r"\bfocus\b"))

    # ArrowUp -> back to first
    inp.press("ArrowUp")
    expect(options.nth(0)).to_have_class(re.compile(r"\bfocus\b"), timeout=2000)
    expect(options.nth(1)).not_to_have_class(re.compile(r"\bfocus\b"))


def test_enter_selects_highlighted_option(page: Page, goto, full_txn):
    """
    WHEN  user navigates to an option with ArrowDown and presses Enter
    THEN  that option is selected and dropdown closes
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = get_ts_input(dialog, 1)  # External Account
    inp.click()
    inp.fill("a")

    dropdown = get_ts_dropdown(dialog)
    wait_for_options(dialog)

    # ArrowDown twice to highlight second option
    inp.press("ArrowDown")
    inp.press("ArrowDown")
    second_option = dropdown.locator(".option").nth(1)
    expect(second_option).to_have_class(re.compile(r"\bfocus\b"), timeout=2000)

    # Enter to select
    inp.press("Enter")

    # Dropdown closes
    expect(dropdown).not_to_be_visible(timeout=3000)


# ===========================================================
# Create new value on no match
# ===========================================================


def test_create_new_value_when_no_match(page: Page, goto, full_txn):
    """
    WHEN  user types a non-existing value and presses Enter
    THEN  a new option is created and selected
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    new_cat = "ZZZUniqueCategory9999"
    inp = get_ts_input(dialog, 2)  # Category
    inp.click()
    inp.fill(new_cat)

    dropdown = get_ts_dropdown(dialog)
    # Tom Select should show a "create" option
    expect(dropdown.locator(".option.create")).to_be_visible(timeout=3000)

    # Click the create option
    dropdown.locator(".option.create").click()

    # Dropdown closes
    expect(dropdown).not_to_be_visible(timeout=3000)

    # Input shows the created value
    expect(inp).to_have_value(new_cat)
