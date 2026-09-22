"""
Story-based UI tests for transaction category splits.

Three end-to-end flows:
  Story A: Add and remove a single split
  Story B: Multiple splits + validation errors
  Story C: Build three splits, delete mid-sequence
"""

from playwright.sync_api import Page, expect


def open_modal(page: Page, txn_id: int):
    """Click Edit on the row and wait for the modal dialog to open."""
    row = page.locator(f"#txn-{txn_id}")
    row.locator("button", has_text="Edit").click()
    dialog = page.locator(f"#transaction-edit-modal-{txn_id}")
    expect(dialog).to_be_visible()
    return dialog


def close_modal(page: Page, txn_id: int):
    """Press Escape and wait for the modal container to empty."""
    page.keyboard.press("Escape")
    expect(page.locator("#edit-modal-container")).to_be_empty(timeout=3000)


def new_amount_input(split_section, txn_id: int):
    """Locator for the add-split amount input (never ambiguous)."""
    return split_section.locator(f"#add-split-{txn_id} input[name='amount_dollars']")


def add_split_btn(split_section):
    """Locator for the Add Split button."""
    return split_section.locator("button", has_text="Add Split")


def remainder_row(split_section):
    """Locator for the remainder row."""
    return split_section.locator("[data-remainder-row]")


def set_split_category(page: Page, select_locator, name: str):
    """Pick a split category through its Tom Select instance.

    Tom Select hides the native <select>, so Playwright's select_option() cannot
    drive it. setValue() fires the same onChange path (including the PATCH) as a
    real selection.
    """
    select_locator.evaluate("(el, name) => el.tomselect.setValue(name)", name)
    page.wait_for_load_state("networkidle")


# ============================================================
# Story A: "Add and remove a split"
# ============================================================


def test_story_a_add_and_remove_split(page: Page, goto, txn_for_splitting):
    """
    Complete lifecycle of a single split on a fresh transaction.
    """
    txn_id = txn_for_splitting["txn_id"]
    goto("/inbox")

    # --- Open modal ---
    dialog = open_modal(page, txn_id)
    split_section = dialog.locator("#splits-section-" + str(txn_id))
    expect(split_section).to_be_visible()

    add_btn = add_split_btn(split_section)
    expect(add_btn).to_be_disabled()

    # Type an amount equal to the total -> still disabled (no remainder)
    inp = new_amount_input(split_section, txn_id)
    inp.fill("125.00")
    expect(add_btn).to_be_disabled()

    # Type a valid amount ($50.00) -> button enabled
    inp.fill("50.00")
    expect(add_btn).to_be_enabled()

    # --- Add the split (no category) ---
    add_btn.click()
    page.wait_for_load_state("networkidle")

    # Split row + remainder row should appear
    expect(remainder_row(split_section)).to_be_visible()

    # Set category on the split row to "Groceries"
    split_select = split_section.locator("[data-split-row] select").first
    set_split_category(page, split_select, "Groceries")

    # --- Close and reopen modal to verify persistence ---
    close_modal(page, txn_id)
    dialog = open_modal(page, txn_id)
    split_section = dialog.locator("#splits-section-" + str(txn_id))
    expect(remainder_row(split_section)).to_be_visible()
    # The select should show Groceries as the selected value
    first_select = split_section.locator("[data-split-row] select").first
    expect(first_select).to_have_value("Groceries")

    # --- Delete the split ---
    delete_btn = split_section.locator("button[hx-delete]")
    delete_btn.click()
    page.wait_for_load_state("networkidle")

    # Remainder row should be gone, form back to clean state
    expect(remainder_row(split_section)).not_to_be_visible()

    # --- Close modal -> row refreshes ---
    close_modal(page, txn_id)
    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_be_visible()


# ============================================================
# Story B: "Multiple splits and edit validation"
# ============================================================


def test_story_b_multiple_splits_and_validation(page: Page, goto, txn_for_splitting):
    """
    Build multiple splits, hit Alpine gate (client-side) and 422 (server-side).
    """
    txn_id = txn_for_splitting["txn_id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)
    split_section = dialog.locator("#splits-section-" + str(txn_id))

    # --- Add first split: $80.00 Entertainment ---
    inp = new_amount_input(split_section, txn_id)
    inp.fill("80.00")
    add_split_btn(split_section).click()
    page.wait_for_load_state("networkidle")
    expect(remainder_row(split_section)).to_be_visible()

    # Category select on the first existing split row
    split_category = split_section.locator("[data-split-row] select").first
    set_split_category(page, split_category, "Entertainment")

    # --- Attempt second split exceeding remainder -> Alpine gate disabled ---
    add_btn = add_split_btn(split_section)
    inp.fill("120.00")
    expect(add_btn).to_be_disabled()

    # --- Add valid second split: $30.00 Groceries ---
    inp.fill("30.00")
    expect(add_btn).to_be_enabled()
    add_btn.click()
    page.wait_for_load_state("networkidle")

    # Should now see two splits
    expect(split_section.locator("[data-split-row]")).to_have_count(2)

    # --- Edit first split to consume total -> PATCH 422 ---
    first_amount = split_section.locator("input[name='amount_dollars']").first
    first_amount.fill("125.00")
    first_amount.blur()
    page.wait_for_load_state("networkidle")

    # Split section should still be present (error shown, value reverted)
    expect(split_section).to_be_visible()

    # --- Edit first split to valid value ---
    first_amount.fill("70.00")
    first_amount.blur()
    page.wait_for_load_state("networkidle")

    # --- Close modal -> row refreshes ---
    close_modal(page, txn_id)
    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_be_visible()


# ============================================================
# Story C: "Three-split transaction"
# ============================================================


def test_story_c_three_split_transaction(page: Page, goto, txn_for_splitting):
    """
    Build three splits sequentially, verify remainder math, delete mid-sequence.
    """
    txn_id = txn_for_splitting["txn_id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)
    split_section = dialog.locator("#splits-section-" + str(txn_id))
    inp = new_amount_input(split_section, txn_id)
    add_btn = add_split_btn(split_section)

    # --- Add $50.00 ---
    inp.fill("50.00")
    expect(add_btn).to_be_enabled()
    add_btn.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)  # let Alpine re-initialise the swapped section

    # --- Add $40.00 ---
    inp.fill("40.00")
    expect(add_btn).to_be_enabled()
    add_btn.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)

    # --- Add $20.00 ---
    inp.fill("20.00")
    expect(add_btn).to_be_enabled()
    add_btn.click()
    page.wait_for_load_state("networkidle")

    # Should have 3 split rows
    expect(split_section.locator("[data-split-row]")).to_have_count(3)

    # --- Attempt 4th split ($20.00) -> Alpine gate disabled (remainder $15) ---
    inp.fill("20.00")
    expect(add_btn).to_be_disabled()

    # --- Delete the middle split (index 1) ---
    delete_btns = split_section.locator("button[hx-delete]")
    expect(delete_btns).to_have_count(3)
    delete_btns.nth(1).click()
    page.wait_for_load_state("networkidle")

    # Should now have 2 splits
    expect(split_section.locator("[data-split-row]")).to_have_count(2)

    # --- Close modal -> row refreshes ---
    close_modal(page, txn_id)
    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_be_visible()
