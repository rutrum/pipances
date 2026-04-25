"""
UI tests for the inbox transaction edit modal — written from scratch.

Edit flow per spec:
  1. Click Edit on a row → modal opens
  2. Change a field (combo box: type value, click dropdown item to save)
  3. Close modal (Escape or backdrop click)
  4. The TABLE ROW reflects the change (row is re-fetched from server on close)

Each small test verifies one field in isolation.
test_sequential_edits_accumulate is a multi-step test verifying that
repeated open/edit/close cycles don't wipe prior field values.

Known bugs that will cause failures:
  BUG-A: txn_id is empty in _combo_edit.html hx-get URL
         (/api/combo/descriptions?txn_id=&field=description)
         → combo dropdown items fire PATCH to /transactions/ (404/422)
         → field edits are never saved → tests 4a–4e, 4i, 4j will FAIL
  BUG-B: Modal Approve button has no disabled state — it is always enabled
         regardless of description/external presence
         → tests 4g, 4h will FAIL
"""

from playwright.sync_api import Page, expect

# ============================================================
# Helper: fill a combo box inside the modal and select a value
# ============================================================


def fill_combo(dialog, nth: int, value: str):
    """
    Type `value` into the nth .combo-box input inside `dialog`,
    wait for the matching dropdown item to appear, and click it.
    nth=0 → Description, nth=1 → External Account, nth=2 → Category
    """
    combo = dialog.locator(".combo-box").nth(nth)
    inp = combo.locator("input")
    inp.click()
    inp.fill(value)
    # Wait for a dropdown item that contains the value (or "Create X")
    item = dialog.locator(f'[data-combo-item]:has-text("{value}")').first
    expect(item).to_be_visible(timeout=3000)
    item.click()


def open_modal(page: Page, txn_id: int):
    """Click Edit on the row and wait for the modal dialog to open."""
    row = page.locator(f"#txn-{txn_id}")
    row.locator("button", has_text="Edit").click()
    dialog = page.locator(f"#transaction-edit-modal-{txn_id}")
    expect(dialog).to_be_visible()
    return dialog


def close_via_escape(page: Page, txn_id: int):
    """Press Escape and wait for the modal container to empty."""
    page.keyboard.press("Escape")
    expect(page.locator("#edit-modal-container")).to_be_empty(timeout=3000)


def close_via_backdrop(page: Page):
    """Click the top-left corner of the viewport (outside modal box) to close."""
    page.mouse.click(5, 5)
    expect(page.locator("#edit-modal-container")).to_be_empty(timeout=3000)


# ============================================================
# 4a: Edit description → close → row reflects change
# ============================================================


def test_edit_description_persists_after_close(page: Page, goto, full_txn):
    """
    WHEN  user opens modal, changes description, closes
    THEN  the table row shows the new description
    BUG-A: Will FAIL — txn_id empty in combo, PATCH goes to /transactions/
    """
    txn_id = full_txn["id"]
    new_desc = full_txn["alt_description"]

    goto("/inbox")
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 0, new_desc)
    close_via_escape(page, txn_id)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text(new_desc, timeout=3000)


# ============================================================
# 4b: Edit category → close → row reflects change
# ============================================================


def test_edit_category_persists_after_close(page: Page, goto, full_txn):
    """
    WHEN  user opens modal, changes category, closes
    THEN  the table row shows the new category
    BUG-A: Will FAIL — same txn_id bug
    """
    txn_id = full_txn["id"]
    new_cat = full_txn["alt_cat_name"]

    goto("/inbox")
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 2, new_cat)
    close_via_escape(page, txn_id)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text(new_cat, timeout=3000)


# ============================================================
# 4c: Edit external account → close → row reflects change
# ============================================================


def test_edit_external_persists_after_close(page: Page, goto, full_txn):
    """
    WHEN  user opens modal, changes external account, closes
    THEN  the table row shows the new external account
    BUG-A: Will FAIL — same txn_id bug
    """
    txn_id = full_txn["id"]
    new_ext = full_txn["alt_ext_name"]

    goto("/inbox")
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 1, new_ext)
    close_via_escape(page, txn_id)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text(new_ext, timeout=3000)


# ============================================================
# 4d: Edit all three fields → close → row reflects all changes
# ============================================================


def test_edit_all_fields_persist_after_close(page: Page, goto, full_txn):
    """
    WHEN  user opens modal, changes description + external + category, closes
    THEN  the table row shows all three updated values
    BUG-A: Will FAIL — same txn_id bug
    """
    txn_id = full_txn["id"]
    new_desc = full_txn["alt_description"]
    new_ext = full_txn["alt_ext_name"]
    new_cat = full_txn["alt_cat_name"]

    goto("/inbox")
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 0, new_desc)
    fill_combo(dialog, 1, new_ext)
    fill_combo(dialog, 2, new_cat)
    close_via_escape(page, txn_id)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text(new_desc, timeout=3000)
    expect(row).to_contain_text(new_ext, timeout=3000)
    expect(row).to_contain_text(new_cat, timeout=3000)


# ============================================================
# 4e: Sequential edits accumulate — the full realistic user journey
#
# This is intentionally one multi-step test: it verifies that each
# open/close cycle does not wipe values set in a prior cycle.
# BUG-A: Will FAIL at step 1 — changes don't save due to txn_id bug.
# ============================================================


def test_sequential_edits_accumulate(page: Page, goto, full_txn):
    """
    Step 1: change description → close → row shows new description
    Step 2: re-open, change category → close → row shows new description AND new category
    Step 3: re-open, change external → close → row shows all three fields updated
    Step 4: re-open, change all three to final values → close → row shows final values
    """
    txn_id = full_txn["id"]
    desc1 = "Step One Description"
    ext1 = full_txn["ext_name"]  # starting external (no change this step)
    cat1 = full_txn["cat_name"]  # starting category (no change this step)
    cat2 = full_txn["alt_cat_name"]
    ext2 = full_txn["alt_ext_name"]
    final_desc = "Final Description"
    final_ext = full_txn["alt_ext_name"]
    final_cat = full_txn["alt_cat_name"]

    goto("/inbox")

    # --- Step 1: change description only ---
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 0, desc1)
    close_via_escape(page, txn_id)
    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text(desc1, timeout=3000)

    # --- Step 2: change category, description must still be there ---
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 2, cat2)
    close_via_escape(page, txn_id)
    expect(row).to_contain_text(desc1, timeout=3000)  # still there
    expect(row).to_contain_text(cat2, timeout=3000)

    # --- Step 3: change external, desc + cat must still be there ---
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 1, ext2)
    close_via_escape(page, txn_id)
    expect(row).to_contain_text(desc1, timeout=3000)  # still there
    expect(row).to_contain_text(cat2, timeout=3000)  # still there
    expect(row).to_contain_text(ext2, timeout=3000)

    # --- Step 4: change all three to final values ---
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 0, final_desc)
    fill_combo(dialog, 1, final_ext)
    fill_combo(dialog, 2, final_cat)
    close_via_escape(page, txn_id)
    expect(row).to_contain_text(final_desc, timeout=3000)
    expect(row).to_contain_text(final_ext, timeout=3000)
    expect(row).to_contain_text(final_cat, timeout=3000)


# ============================================================
# 4f: Approve from modal → modal auto-closes → row shows Approved
# ============================================================


def test_approve_from_modal_closes_and_updates_row(
    page: Page, goto, description_and_external_txn
):
    """
    GIVEN a transaction with description + external set
    WHEN  user opens edit modal and clicks Approve
    THEN  modal closes automatically
    THEN  the table row shows the 'Approved' button state
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    approve_btn = dialog.locator("button", has_text="Approve")
    expect(approve_btn).to_be_visible()
    approve_btn.click()

    # Modal should close automatically
    expect(page.locator("#edit-modal-container")).to_be_empty(timeout=3000)

    # Row in table should now show the Approved state
    row = page.locator(f"#txn-{txn_id}")
    expect(row.locator("button", has_text="Approved")).to_be_visible()


# ============================================================
# 4g: Approve button in modal disabled when description is missing
# ============================================================


def test_modal_approve_btn_disabled_no_description(page: Page, goto):
    """
    GIVEN a transaction with no description (and no external)
    WHEN  user opens the edit modal
    THEN  the Approve button inside the modal is disabled
    BUG-B: Will FAIL — modal always renders an enabled Approve button
    """
    goto("/inbox")
    # Use the seeded row that has no description
    no_desc_row = (
        page.locator("#inbox-table tr").filter(has_text="no description").first
    )
    expect(no_desc_row).to_be_visible()
    no_desc_row.locator("button", has_text="Edit").click()

    dialog = page.locator("dialog")
    expect(dialog).to_be_visible()
    approve_btn = dialog.locator("button", has_text="Approve")
    expect(approve_btn).to_be_disabled()


# ============================================================
# 4h: Approve button in modal disabled when external is missing
# ============================================================


def test_modal_approve_btn_disabled_no_external(page: Page, goto, description_only_txn):
    """
    GIVEN a transaction with description set but external NULL
    WHEN  user opens the edit modal
    THEN  the Approve button inside the modal is disabled
    BUG-B: Will FAIL — modal always renders an enabled Approve button
    """
    txn_id = description_only_txn
    goto("/inbox")
    dialog = open_modal(page, txn_id)
    approve_btn = dialog.locator("button", has_text="Approve")
    expect(approve_btn).to_be_disabled()


# ============================================================
# Combo box: select existing value by typing partial text
# ============================================================


def test_combo_select_existing_external_by_partial_type(page: Page, goto, full_txn):
    """
    WHEN  user types partial text ("Net") in the external account combo
    THEN  "Netflix" appears in the dropdown
    WHEN  user clicks "Netflix"
    THEN  the dropdown closes
    THEN  the input shows "Netflix"
    THEN  the modal stays open
    THEN  row shows "Netflix" as the external account after close
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = dialog.locator(".combo-box").nth(1).locator("input")
    inp.click()
    inp.fill("Net")

    netflix_item = dialog.locator('[data-combo-item]:has-text("Netflix")').first
    expect(netflix_item).to_be_visible(timeout=3000)
    netflix_item.click()

    # Dropdown must close
    expect(netflix_item).not_to_be_visible(timeout=3000)
    # Input must show the selected value
    expect(inp).to_have_value("Netflix")
    # Modal must stay open
    expect(dialog).to_be_visible()

    close_via_escape(page, txn_id)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text("Netflix", timeout=3000)


# ============================================================
# Combo box: create a brand-new value via the "+" option
# ============================================================


def test_combo_create_new_external_account(page: Page, goto, full_txn):
    """
    WHEN  user types a name that does not exist ("Walmart")
    THEN  a '+ Create "Walmart"' option appears in the dropdown
    WHEN  user clicks it
    THEN  the dropdown closes
    THEN  the input shows "Walmart"
    THEN  the modal stays open
    THEN  the new account is created and the row shows "Walmart" after close
    """
    txn_id = full_txn["id"]
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    inp = dialog.locator(".combo-box").nth(1).locator("input")
    inp.click()
    inp.fill("Walmart")

    create_item = dialog.locator('[data-combo-item]:has-text("Create")').first
    expect(create_item).to_be_visible(timeout=3000)
    create_item.click()

    # Dropdown must close
    expect(create_item).not_to_be_visible(timeout=3000)
    # Input must show the created value
    expect(inp).to_have_value("Walmart")
    # Modal must stay open
    expect(dialog).to_be_visible()

    close_via_escape(page, txn_id)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text("Walmart", timeout=3000)


def test_close_via_escape_refreshes_row(page: Page, goto, full_txn):
    """
    WHEN  user edits description in modal then closes via Escape
    THEN  the table row reflects the saved description
    BUG-A: Will FAIL — edit doesn't save (txn_id empty in combo)
    """
    txn_id = full_txn["id"]
    new_desc = full_txn["alt_description"]

    goto("/inbox")
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 0, new_desc)
    close_via_escape(page, txn_id)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text(new_desc, timeout=3000)


# ============================================================
# 4j: Close via backdrop click — row is refreshed with saved data
# ============================================================


def test_close_via_backdrop_refreshes_row(page: Page, goto, full_txn):
    """
    WHEN  user edits description in modal then closes via backdrop click
    THEN  the table row reflects the saved description
    BUG-A: Will FAIL — edit doesn't save (txn_id empty in combo)
    """
    txn_id = full_txn["id"]
    new_desc = full_txn["alt_description"]

    goto("/inbox")
    dialog = open_modal(page, txn_id)
    fill_combo(dialog, 0, new_desc)
    close_via_backdrop(page)

    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_contain_text(new_desc, timeout=3000)


# ============================================================


# ============================================================
# Approve button OOB update after filling description + external
# ============================================================


def test_approve_btn_enables_after_filling_both_fields(
    page: Page, goto, description_only_txn
):
    """
    GIVEN  a transaction that has a description but NO external account
    WHEN   user opens the edit modal
    THEN   the Approve button is disabled

    WHEN   user sets the external account via the combo box
    THEN   the combo PATCH fires, the row updates, AND the modal's Approve
           button is updated via OOB swap and becomes enabled
    """
    txn_id = description_only_txn
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    approve_btn = dialog.locator(".btn-lg")

    # Approve is disabled — description set but external missing
    expect(approve_btn).to_be_disabled()

    # Fill in external account via combo
    fill_combo(dialog, 1, "Aldi")

    # After the PATCH response, Approve button should now be enabled
    expect(approve_btn).to_be_enabled(timeout=3000)
    expect(approve_btn).not_to_have_attribute("disabled", "")


def test_approve_btn_disables_after_clearing_external(
    page: Page, goto, description_and_external_txn
):
    """
    GIVEN  a transaction with both description AND external set
    WHEN   user opens the edit modal
    THEN   the Approve button is enabled

    WHEN   user clears the external account (selects Clear from combo)
    THEN   the combo PATCH fires and the modal's Approve button is updated
           via OOB and becomes disabled
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    dialog = open_modal(page, txn_id)

    approve_btn = dialog.locator(".btn-lg")

    # Both fields set → Approve is enabled
    expect(approve_btn).to_be_enabled()

    # Clear the external account — type nothing and wait for Clear option
    ext_input = dialog.locator(".combo-box").nth(1).locator("input")
    ext_input.click()
    ext_input.clear()
    page.wait_for_load_state("networkidle")

    clear_item = dialog.locator('[data-combo-item][data-combo-value=""]')
    expect(clear_item).to_be_visible(timeout=3000)
    clear_item.click()
    page.wait_for_load_state("networkidle")

    # After clearing external, Approve button should be disabled
    expect(approve_btn).to_be_disabled(timeout=3000)
