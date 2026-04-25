"""
UI tests for the individual row Approve button in the inbox.

Business rules under test:
  - Both description AND external are required to enable Approve
  - Category is the only nullable field
  - Clicking Approve marks the row — it does NOT change the inbox badge
    (badge only changes on commit)
  - Approved/Approve is a toggle: clicking Approved reverts back
  - approved state is persisted to DB (survives page refresh)

Fixtures:
  description_only_txn    — description set, external NULL  → Approve should be DISABLED
  description_and_external_txn — description + external set, category NULL → Approve ENABLED
"""

import re

from playwright.sync_api import Page, expect

# ============================================================
# 3a: Disabled — no description, no external
# ============================================================


def test_approve_btn_disabled_no_description(page: Page, goto):
    """
    GIVEN a pending transaction with no description and no external
    THEN  its Approve button is disabled
    """
    goto("/inbox")
    # The seeded "UNKNOWN RETAIL STORE" row has neither description nor external
    no_desc_row = (
        page.locator("#inbox-table tr").filter(has_text="no description").first
    )
    expect(no_desc_row).to_be_visible()
    approve_btn = no_desc_row.locator("button", has_text="Approve")
    expect(approve_btn).to_be_disabled()


# ============================================================
# 3b: Disabled — description set but external is NULL
# ============================================================


def test_approve_btn_disabled_description_only_no_external(
    page: Page, goto, description_only_txn
):
    """
    GIVEN a pending transaction with description set but external_id NULL
    THEN  its Approve button is disabled
    BUG:  Row template currently only checks txn.description — external is NOT
          checked.  This test is expected to FAIL until the template is fixed.
    """
    txn_id = description_only_txn
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_be_visible()
    approve_btn = row.locator("button", has_text="Approve")
    expect(approve_btn).to_be_disabled()


# ============================================================
# 3c: Enabled — description + external set, category NULL
# ============================================================


def test_approve_btn_enabled_description_and_external(
    page: Page, goto, description_and_external_txn
):
    """
    GIVEN a pending transaction with description and external set, category NULL
    THEN  its Approve button is enabled and visible
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")
    expect(row).to_be_visible()
    approve_btn = row.locator("button[hx-patch]", has_text="Approve")
    expect(approve_btn).to_be_enabled()
    expect(approve_btn).to_be_visible()


# ============================================================
# 3d: Click Approve — row updates in place
# ============================================================


def test_approve_click_flips_row_to_approved(
    page: Page, goto, description_and_external_txn
):
    """
    GIVEN an eligible row
    WHEN  user clicks Approve
    THEN  the button changes to 'Approved' (no page reload)
    THEN  the row gets the approved visual style
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")
    row.locator("button[hx-patch]", has_text="Approve").click()

    # Row re-renders in place — wait for the Approved button to appear
    expect(row.locator("button", has_text="Approved")).to_be_visible()
    # Row should have the approved background style
    expect(row).to_have_class(re.compile(r"bg-success"))


# ============================================================
# 3f: Category NULL is allowed — approve still works
# ============================================================


def test_approve_succeeds_with_null_category(
    page: Page, goto, description_and_external_txn
):
    """
    GIVEN a pending transaction with description + external but NO category
    THEN  clicking Approve succeeds (category is optional)
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")
    row.locator("button[hx-patch]", has_text="Approve").click()
    expect(row.locator("button", has_text="Approved")).to_be_visible()


# ============================================================
# 3g: Unapprove — clicking Approved reverts the row
# ============================================================


def test_approved_btn_click_reverts_to_approve(
    page: Page, goto, description_and_external_txn
):
    """
    GIVEN a row that has been approved
    WHEN  user clicks the 'Approved' button
    THEN  the row reverts to showing 'Approve'
    THEN  the approved background styling is removed
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")

    # Approve first
    row.locator("button[hx-patch]", has_text="Approve").click()
    expect(row.locator("button", has_text="Approved")).to_be_visible()

    # Now unapprove
    row.locator("button", has_text="Approved").click()
    expect(row.locator("button[hx-patch]", has_text="Approve")).to_be_visible()
    expect(row).not_to_have_class(re.compile(r"bg-success"))


# ============================================================
# 3h: Re-approve after unapprove
# ============================================================


def test_reapprove_after_unapprove(page: Page, goto, description_and_external_txn):
    """
    GIVEN the full approve → unapprove → approve cycle
    THEN  the row ends in the Approved state with no errors
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")

    row.locator("button[hx-patch]", has_text="Approve").click()
    expect(row.locator("button", has_text="Approved")).to_be_visible()

    row.locator("button", has_text="Approved").click()
    expect(row.locator("button[hx-patch]", has_text="Approve")).to_be_visible()

    row.locator("button[hx-patch]", has_text="Approve").click()
    expect(row.locator("button", has_text="Approved")).to_be_visible()


# ============================================================
# 3i: Approved state persists across page refresh
# ============================================================


def test_approved_state_persists_on_page_refresh(
    page: Page, goto, description_and_external_txn
):
    """
    GIVEN user clicks Approve
    WHEN  the page is fully reloaded
    THEN  the row still shows the 'Approved' state
    (verifies marked_for_approval is written to DB, not just client state)
    """
    txn_id, _ext_name = description_and_external_txn
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")
    row.locator("button[hx-patch]", has_text="Approve").click()
    expect(row.locator("button", has_text="Approved")).to_be_visible()

    # Full reload
    goto("/inbox")
    row = page.locator(f"#txn-{txn_id}")
    expect(row.locator("button", has_text="Approved")).to_be_visible()
