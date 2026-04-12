"""
UI tests for the commit confirmation flow.

Covers openspec/specs/commit-confirmation/spec.md in full, plus
regression coverage for the multi-page table-dump bug (commit endpoint
previously returned all remaining rows instead of one page).

Test isolation: each test uses `approvable_txn` which marks one pending
transaction with a description, then fully restores it (including status)
after the test — so the session DB always has a consistent 20 pending
transactions at the start of each test.
"""

from playwright.sync_api import Page, expect

from tests.ui.helpers import (
    badge_count,
    cancel_commit,
    confirm_commit,
    do_approve,
    expected_pages,
    inbox_page_label,
    open_commit_dialog,
)

# ============================================================
# Scenario: No approved transactions
# ============================================================


def test_commit_with_nothing_approved_shows_toast_not_dialog(page: Page, goto):
    """
    WHEN  user clicks Commit but no transactions are marked for approval
    THEN  a warning toast appears
    THEN  no dialog appears
    """
    goto("/inbox")
    page.click("button:text('Commit')")
    expect(page.locator("#toast-container")).to_contain_text("Nothing to commit")
    expect(page.locator("#commit-dialog-container")).to_be_empty()


# ============================================================
# Scenario: Confirmation dialog content
# ============================================================


def test_dialog_shows_transaction_count(page: Page, goto, approvable_txn):
    """
    WHEN  user clicks Commit with 1 approved transaction
    THEN  modal shows "Commit 1 transaction"
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    expect(page.locator("#commit-dialog-container")).to_contain_text(
        "Commit 1 transaction"
    )


def test_dialog_no_new_entities_message(page: Page, goto, approvable_txn):
    """
    WHEN  all referenced categories and external accounts already exist
    THEN  dialog shows 'No new categories or accounts will be created'
    THEN  new categories section is absent
    THEN  new external accounts section is absent

    The approvable_txn fixture creates a transaction with no category and no
    external account, so nothing new would be created on commit.
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    expect(page.locator("#commit-dialog-container")).to_contain_text(
        "No new categories or accounts will be created"
    )
    expect(page.locator("#commit-dialog-container")).not_to_contain_text(
        "New categories"
    )
    expect(page.locator("#commit-dialog-container")).not_to_contain_text(
        "New external accounts"
    )


def test_dialog_lists_new_categories(
    page: Page, goto, approvable_txn_with_new_category
):
    """
    WHEN  an approved transaction references a category not yet on any approved txn
    THEN  dialog lists that category under 'New categories'
    """
    _txn_id, category_name = approvable_txn_with_new_category
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    expect(page.locator("#commit-dialog-container")).to_contain_text("New categories")
    expect(page.locator("#commit-dialog-container")).to_contain_text(category_name)


# ============================================================
# Scenario: User cancels commit
# ============================================================


def test_cancel_closes_dialog(page: Page, goto, approvable_txn):
    """
    WHEN  user clicks Cancel
    THEN  dialog closes
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    cancel_commit(page)
    expect(page.locator("#commit-dialog-container")).to_be_empty()


def test_cancel_does_not_commit(page: Page, goto, approvable_txn):
    """
    WHEN  user clicks Cancel
    THEN  badge count is unchanged (transaction remains pending)
    """
    goto("/inbox")
    count_before = badge_count(page)
    do_approve(page)
    open_commit_dialog(page)
    cancel_commit(page)
    assert badge_count(page) == count_before


# ============================================================
# Scenario: User confirms commit
# ============================================================


def test_confirm_closes_dialog(page: Page, goto, approvable_txn):
    """
    WHEN  user clicks Confirm
    THEN  dialog closes
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)
    expect(page.locator("#commit-dialog-container")).to_be_empty()


def test_confirm_shows_success_toast(page: Page, goto, approvable_txn):
    """
    WHEN  user clicks Confirm
    THEN  a success toast appears with the committed count
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)
    expect(page.locator("#toast-container")).to_contain_text("Committed")


def test_confirm_decrements_badge(page: Page, goto, approvable_txn):
    """
    WHEN  user commits 1 transaction
    THEN  the inbox badge decrements by 1
    """
    goto("/inbox")
    count_before = badge_count(page)
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)
    expect(page.locator("#toast-container")).to_contain_text("Committed")
    assert badge_count(page) == count_before - 1


def test_confirm_removes_committed_rows_from_table(page: Page, goto, approvable_txn):
    """
    WHEN  user commits approved transactions
    THEN  those rows no longer appear in the inbox table
    """
    goto("/inbox")
    rows_before = page.locator("#inbox-table tr").count()
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)
    rows_after = page.locator("#inbox-table tr").count()
    assert rows_after < rows_before, (
        f"Expected fewer rows after commit ({rows_after} >= {rows_before})"
    )


# ============================================================
# Multi-page: table must respect page_size after commit
# ============================================================


def test_confirm_table_respects_page_size(page: Page, goto, bulk_pending_txns):
    """
    Regression: commit endpoint previously had no .limit(), dumping all
    remaining pending transactions into #inbox-table regardless of page_size.

    Setup: seed (20) + fixture (10) = 30 pending; page_size=25 (default).
    After committing 1, 29 remain. Table must show exactly 25 rows (page 1),
    not all 29.
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)

    rows = page.locator("#inbox-table tr").count()
    assert rows <= 25, (
        f"Expected ≤25 rows (page_size=25), got {rows} — "
        "commit is dumping all remaining rows instead of one page"
    )


def test_confirm_pagination_resets_to_page_one(page: Page, goto, approvable_txn):
    """
    WHEN  user commits from any page
    THEN  inbox pagination resets to page 1
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)
    expect(inbox_page_label(page, 1)).to_be_visible()


def test_confirm_pagination_total_reflects_remaining(
    page: Page, goto, bulk_pending_txns
):
    """
    WHEN  user commits 1 transaction
    THEN  pagination total reflects the new remaining count

    Setup: 30 pending (seed 20 + fixture 10), page_size=25 (default).
    After committing 1: 29 remaining → ceil(29/25) = 2 pages → "Page 1 of 2".
    Reads badge before committing so the assertion doesn't hardcode seed numbers.
    """
    goto("/inbox")
    remaining_before = badge_count(page)

    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)

    remaining_after = remaining_before - 1
    pages = expected_pages(remaining_after, page_size=25)
    expect(
        page.locator(f"#inbox-pagination span:has-text('Page 1 of {pages}')")
    ).to_be_visible()
