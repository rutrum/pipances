"""
Regression tests for OOB swap fragility bugs.

Bug 1: Pagination disappears after clicking Next on /data/transactions.
  Root cause: _pagination.html always emitted hx-swap-oob, so HTMX stripped
  the pagination element from the primary swap target (#data-content) and then
  couldn't find the OOB target because it was inside the replaced element.

Bug 2: Commit modal doesn't dismiss and table doesn't update after confirming.
  Root cause: pagination_id was missing from inbox.py OOB render calls,
  producing hx-swap-oob="outerHTML:#" (invalid selector) which threw a JS
  error and halted all remaining OOB processing including dialog_clear.
  Additionally, commit-summary crashed with 500 when a transaction had no
  external account (txn.external.name on None).
"""

from playwright.sync_api import Page, expect

from tests.ui.helpers import (
    confirm_commit,
    data_page_label,
    data_pagination,
    do_approve,
    open_commit_dialog,
)

# ============================================================
# Bug 1: Pagination persists after navigating pages
# ============================================================


def test_data_transactions_pagination_visible_on_load(page: Page, goto):
    """Baseline: pagination renders on initial page load."""
    goto("/data/transactions")
    expect(data_pagination(page)).to_be_visible()
    expect(data_page_label(page, 1)).to_be_visible()


def test_data_transactions_pagination_persists_after_next(page: Page, goto):
    """
    Regression: clicking Next must not make the pagination disappear.

    Before fix: _pagination.html had unconditional hx-swap-oob. HTMX stripped
    the element from the primary response and then couldn't find the OOB target
    (it was inside #data-content which had just been replaced). Pagination
    silently vanished from the DOM.
    """
    goto("/data/transactions")
    page.click("button:text('Next »')")
    expect(data_page_label(page, 2)).to_be_visible()
    expect(data_pagination(page)).to_be_visible()


def test_data_transactions_pagination_persists_after_multiple_pages(page: Page, goto):
    """Pagination survives multiple sequential page navigations."""
    goto("/data/transactions")
    page.click("button:text('Next »')")
    expect(data_page_label(page, 2)).to_be_visible()
    page.click("button:text('Next »')")
    expect(data_page_label(page, 3)).to_be_visible()
    expect(data_pagination(page)).to_be_visible()


def test_data_transactions_prev_button_updates_pagination(page: Page, goto):
    """Prev button also keeps pagination intact."""
    goto("/data/transactions?page=3")
    page.click("button:text('« Prev')")
    expect(data_page_label(page, 2)).to_be_visible()
    expect(data_pagination(page)).to_be_visible()


# ============================================================
# Bug 2: Commit modal dismisses and table updates
# ============================================================


def test_commit_modal_appears_when_approved_transactions_exist(
    page: Page, goto, approvable_txn
):
    """Baseline: commit button opens a modal when approved transactions exist."""
    goto("/inbox")
    do_approve(page)
    page.click("button:text('Commit')")
    expect(page.locator("#commit-dialog-container dialog")).to_be_visible()
    expect(page.locator("#commit-dialog-container")).to_contain_text("Commit")


def test_commit_modal_dismisses_on_cancel(page: Page, goto, approvable_txn):
    """Clicking Cancel closes the dialog without committing."""
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    page.click("button:text('Cancel')")
    expect(page.locator("#commit-dialog-container")).to_be_empty()


def test_commit_modal_dismisses_after_confirm(page: Page, goto, approvable_txn):
    """
    Regression: modal must close after clicking Confirm.

    Before fix: missing pagination_id in inbox.py caused hx-swap-oob="outerHTML:#"
    (invalid selector). HTMX threw a JS error processing the pagination OOB element,
    halting all subsequent OOB processing — including the dialog_clear fragment —
    so the modal remained open.
    """
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)
    expect(page.locator("#commit-dialog-container")).to_be_empty()


def test_commit_table_updates_after_confirm(page: Page, goto, approvable_txn):
    """
    Regression: committed rows must leave the inbox table after confirming.

    Before fix: the JS error from invalid pagination OOB also prevented the
    primary swap on #inbox-table from running, so committed rows stayed visible.
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


def test_commit_toast_appears_after_confirm(page: Page, goto, approvable_txn):
    """A success toast is shown after a successful commit."""
    goto("/inbox")
    do_approve(page)
    open_commit_dialog(page)
    confirm_commit(page)
    expect(page.locator("#toast-container")).to_contain_text("Committed")


def test_commit_no_approved_shows_warning_not_modal(page: Page, goto):
    """
    Clicking Commit with nothing approved shows a warning toast, not a modal.
    The seed DB starts with no marked_for_approval transactions so this
    exercises the guard path in commit-summary.
    """
    goto("/inbox")
    page.click("button:text('Commit')")
    expect(page.locator("#commit-dialog-container")).to_be_empty()
    expect(page.locator("#toast-container")).to_contain_text("Nothing to commit")
