"""
Story-based UI tests for transaction category splits.

Three end-to-end flows:
  Story A: Add and remove a single split
  Story B: Multiple splits + validation errors
  Story C: Build three splits, delete mid-sequence

All tests open the modal on whatever row the table shows first, then
read the transaction amount from the modal to compute valid split amounts.

Synchronization notes:
- Filling uses Playwright's `fill()` (trusted input events), which Alpine's
  x-model picks up natively. Never set input values via `evaluate` with
  synthetic events: after every split mutation the whole section is swapped
  via HTMX, and a synthetic fill can land on the detached input.
- Every section-mutating action (add/delete/edit split) re-renders the
  section via HTMX outerHTML. Synchronize by polling the resulting DOM with
  `expect(...)` (row counts, re-rendered values) instead of networkidle.
"""

from playwright.sync_api import Page, expect


def open_modal(page: Page):
    """Click Edit on the first table row and wait for the modal dialog to open."""
    page.locator('#inbox-table button:text-is("Edit")').first.click()
    dialog = page.locator("#edit-modal-container dialog")
    expect(dialog).to_be_visible()
    return dialog


def get_txn_id_from_modal(dialog) -> int:
    """Extract the transaction ID from the modal's data-txn-id attribute."""
    box = dialog.locator(".modal-box")
    return int(box.get_attribute("data-txn-id"))


def get_txn_total_from_modal(page: Page, txn_id: int) -> float:
    """Read the absolute transaction amount from the modal's context table."""
    text = page.evaluate(
        f"""() => {{
            const rows = document.querySelector('#splits-section-{txn_id}')
                .closest('.modal-box')
                .querySelectorAll('.table-zebra tr');
            const td = rows[1] ? rows[1].querySelector('td:last-child') : null;
            return td ? td.textContent.trim() : '0';
        }}"""
    )
    return abs(float(text))


def close_modal(page: Page):
    """Press Escape and wait for the modal container to empty."""
    page.keyboard.press("Escape")
    expect(page.locator("#edit-modal-container")).to_be_empty(timeout=3000)


def fill_split_amount(page: Page, txn_id: int, value: str):
    """Fill the add-split amount input.

    Playwright's fill() dispatches trusted input events, so Alpine's
    x-model binding updates `canAdd` immediately. If a section swap from a
    previous action replaces the input mid-fill, Playwright re-resolves the
    locator and retries on the new element.
    """
    page.locator(f"#add-split-{txn_id} input[name='amount_dollars']").fill(value)


def add_split_btn(split_section):
    """Locator for the Add Split button."""
    return split_section.locator("button", has_text="Add Split")


def remainder_row(split_section):
    """Locator for the remainder row."""
    return split_section.locator("[data-remainder-row]")


def split_rows(split_section):
    """Locator for existing split rows."""
    return split_section.locator("[data-split-row]")


# ============================================================
# Story A: "Add and remove a split"
# ============================================================


def test_story_a_add_and_remove_split(page: Page, goto, txn_for_splitting):
    """Complete lifecycle of a single split on a fresh transaction."""
    goto("/inbox")

    dialog = open_modal(page)
    txn_id = get_txn_id_from_modal(dialog)
    # The fixture forces the target transaction to sort first; fail fast if
    # the modal opened on something else (stale state from an earlier story).
    assert txn_id == txn_for_splitting["txn_id"]
    total = get_txn_total_from_modal(page, txn_id)
    split_section = dialog.locator("#splits-section-" + str(txn_id))
    expect(split_section).to_be_visible()

    add_btn = add_split_btn(split_section)
    expect(add_btn).to_be_disabled()

    half = round(total / 2, 2)

    # Amount equal to total -> disabled (no remainder)
    fill_split_amount(page, txn_id, str(total))
    expect(add_btn).to_be_disabled()

    # Valid half amount -> enabled
    fill_split_amount(page, txn_id, str(half))
    expect(add_btn).to_be_enabled()

    # --- Add the split ---
    add_btn.click()
    expect(split_rows(split_section)).to_have_count(1)
    expect(remainder_row(split_section)).to_be_visible()

    # Set category on the split row (PATCH re-renders the section)
    split_select = split_rows(split_section).first.locator("select").first
    split_select.evaluate("(el, name) => el.tomselect.setValue(name)", "Groceries")
    expect(split_rows(split_section).first.locator("select").first).to_have_value(
        "Groceries"
    )

    # --- Close and reopen modal to verify persistence ---
    close_modal(page)
    dialog = open_modal(page)
    split_section = dialog.locator("#splits-section-" + str(txn_id))
    expect(remainder_row(split_section)).to_be_visible()
    first_select = split_rows(split_section).first.locator("select").first
    expect(first_select).to_have_value("Groceries")

    # --- Delete the split ---
    split_section.locator("button[hx-delete]").click()
    expect(split_rows(split_section)).to_have_count(0)

    close_modal(page)
    expect(page.locator("#inbox-table")).to_be_visible()


# ============================================================
# Story B: "Multiple splits and edit validation"
# ============================================================


def test_story_b_multiple_splits_and_validation(page: Page, goto, txn_for_splitting):
    """Build multiple splits, hit Alpine gate (client-side) and 422 (server-side)."""
    goto("/inbox")
    dialog = open_modal(page)
    txn_id = get_txn_id_from_modal(dialog)
    assert txn_id == txn_for_splitting["txn_id"]
    total = get_txn_total_from_modal(page, txn_id)
    split_section = dialog.locator("#splits-section-" + str(txn_id))

    # --- Add first split: ~64% of total ---
    first_split = round(total * 0.64, 2)
    fill_split_amount(page, txn_id, str(first_split))
    add_split_btn(split_section).click()
    expect(split_rows(split_section)).to_have_count(1)

    split_category = split_rows(split_section).first.locator("select").first
    split_category.evaluate(
        "(el, name) => el.tomselect.setValue(name)", "Entertainment"
    )
    expect(split_rows(split_section).first.locator("select").first).to_have_value(
        "Entertainment"
    )

    # --- Exceeding remainder -> disabled ---
    add_btn = add_split_btn(split_section)
    fill_split_amount(page, txn_id, str(total + 10))
    expect(add_btn).to_be_disabled()

    # --- Valid second split ---
    fill_split_amount(page, txn_id, "1.00")
    expect(add_btn).to_be_enabled()
    add_btn.click()
    expect(split_rows(split_section)).to_have_count(2)

    # --- Edit first split to consume total -> PATCH 422 ---
    # The splits section has no hx-target-422, so the error response is
    # discarded and the section (including the input) is left untouched.
    first_amount = split_section.locator("input[name='amount_dollars']").first
    first_amount.fill(f"{total:.2f}")
    first_amount.blur()
    expect(split_rows(split_section)).to_have_count(2)

    # --- Edit first split to a valid value (successful PATCH re-renders) ---
    half = f"{round(total / 2, 2):.2f}"
    first_amount.fill(half)
    first_amount.blur()
    expect(split_section.locator("input[name='amount_dollars']").first).to_have_value(
        half
    )

    close_modal(page)
    expect(page.locator("#inbox-table")).to_be_visible()


# ============================================================
# Story C: "Three-split transaction"
# ============================================================


def test_story_c_three_split_transaction(page: Page, goto, txn_for_splitting):
    """Build three splits sequentially, verify remainder math, delete mid-sequence."""
    goto("/inbox")
    dialog = open_modal(page)
    txn_id = get_txn_id_from_modal(dialog)
    assert txn_id == txn_for_splitting["txn_id"]
    total = get_txn_total_from_modal(page, txn_id)
    split_section = dialog.locator("#splits-section-" + str(txn_id))

    percentages = (0.33, 0.25, 0.10)
    for i, pct in enumerate(percentages, start=1):
        fill_split_amount(page, txn_id, str(round(total * pct, 2)))
        add_split_btn(split_section).click()
        # Add Split swaps the whole section; poll until the new row renders.
        expect(split_rows(split_section)).to_have_count(i)

    # Exceeding remainder -> disabled
    fill_split_amount(page, txn_id, str(total + 10))
    expect(add_split_btn(split_section)).to_be_disabled()

    # Delete the middle split
    delete_btns = split_section.locator("button[hx-delete]")
    expect(delete_btns).to_have_count(len(percentages))
    delete_btns.nth(1).click()
    expect(split_rows(split_section)).to_have_count(len(percentages) - 1)

    close_modal(page)
    expect(page.locator("#inbox-table")).to_be_visible()
