"""
Shared page-helper functions for UI tests.

These are plain functions (not fixtures) that wrap common locator patterns.
Import them directly in test files:

    from tests.ui.helpers import approve_btn, open_commit_dialog, badge_count
"""

from math import ceil

from playwright.sync_api import Page, expect

# === Inbox locators ===


def approve_btn(page: Page):
    """First enabled individual Approve button (has hx-patch; disabled ones don't)."""
    return page.locator("#inbox-table button[hx-patch]:text-is('Approve')").first


def approved_btn(page: Page):
    """First green 'Approved' button — confirms an Approve click was processed."""
    return page.locator("#inbox-table button:text-is('Approved')").first


def inbox_page_label(page: Page, n: int):
    """'Page N of ...' span inside the inbox pagination."""
    return page.locator(f"#inbox-pagination span:has-text('Page {n} of')")


def badge_count(page: Page) -> int:
    """Numeric value shown in the inbox nav badge."""
    return int(page.locator("#inbox-badge span").inner_text().strip())


# === Commit-flow actions ===


def do_approve(page: Page):
    """Click Approve on the first eligible row and wait for it to flip to Approved."""
    approve_btn(page).click()
    expect(approved_btn(page)).to_be_visible()


def open_commit_dialog(page: Page):
    """Click the Commit button and wait for the confirmation dialog to appear."""
    page.click("button:text('Commit')")
    expect(page.locator("#commit-dialog-container dialog")).to_be_visible()


def confirm_commit(page: Page):
    """Click Confirm in the commit dialog and wait for it to close."""
    page.click("button:text('Confirm')")
    expect(page.locator("#commit-dialog-container")).to_be_empty()


def cancel_commit(page: Page):
    """Click Cancel in the commit dialog and wait for it to close."""
    page.click("button:text('Cancel')")
    expect(page.locator("#commit-dialog-container")).to_be_empty()


# === Data transactions locators ===


def data_pagination(page: Page):
    return page.locator("#data-transactions-pagination")


def data_page_label(page: Page, n: int):
    return data_pagination(page).locator(f"span:has-text('Page {n} of')")


# === Pagination maths ===


def expected_pages(total: int, page_size: int) -> int:
    return max(1, ceil(total / page_size))
