"""
UI tests for the read-only Tabulator transactions table on Data > Transactions.

Tabulator provides sorting, arrow rendering, and pagination out of the box, so
these tests deliberately cover only our own wiring:

- the grid mounts with the expected columns,
- our `initialSort` config matches the API default,
- our date-preset control activates and keeps the grid mounted.

Server-side sorting/filtering/pagination is covered by
tests/test_tabulator_table.py.
"""

import re

from playwright.sync_api import Page, expect


def test_transactions_table_renders(page: Page, goto):
    """
    WHEN  user opens Data > Transactions
    THEN  a Tabulator grid renders with the expected columns
    """
    goto("/data/transactions")

    # Tabulator puts the `.tabulator` class on the container itself.
    expect(page.locator("#transactions-table.tabulator")).to_be_visible()
    for title in ("Date", "Amount", "Description", "Category", "External", "Internal"):
        expect(
            page.locator(".tabulator-col-title", has_text=title).first
        ).to_be_visible()


def test_transactions_table_default_sort_is_date_descending(page: Page, goto):
    """
    WHEN  user opens Data > Transactions
    THEN  our `initialSort` config matches the API default (date DESC)
    """
    goto("/data/transactions")

    date_col = page.locator(".tabulator-col", has_text="Date").first
    expect(date_col).to_have_attribute("aria-sort", "descending")


def test_transactions_table_date_preset_reloads_table(page: Page, goto):
    """
    WHEN  user changes the date preset
    THEN  the preset button becomes active and the grid stays rendered
    """
    goto("/data/transactions")

    last_30_btn = page.locator("button:text-is('Last 30 Days')").first
    last_30_btn.click()

    expect(last_30_btn).to_have_class(re.compile("btn-active"))
    expect(page.locator("#transactions-table.tabulator")).to_be_visible()
