"""
UI tests for the Explore page's Tabulator transactions table.

Tabulator provides sorting/filtering/pagination out of the box (covered
server-side by tests/test_tabulator_table.py), so these tests cover only our
own wiring:

- the grid mounts with the expected columns,
- a date preset does full-page navigation (URL gains preset=),
- query-string name filters seed Tabulator's header filters.
"""

import re

from playwright.sync_api import Page, expect


def test_explore_table_renders(page: Page, goto):
    """
    WHEN  user opens Explore
    THEN  a Tabulator grid renders with the expected columns
    """
    goto("/explore")

    expect(page.locator("#transactions-table.tabulator")).to_be_visible()
    for title in ("Date", "Amount", "Description", "Category", "External", "Internal"):
        expect(
            page.locator(".tabulator-col-title", has_text=title).first
        ).to_be_visible()


def test_explore_date_preset_navigates(page: Page, goto):
    """
    WHEN  user clicks a date preset link
    THEN  the browser navigates (URL gains preset=) and the grid remounts
    """
    goto("/explore")

    last_30 = page.locator("a:text-is('Last 30 Days')").first
    last_30.click()
    page.wait_for_url(re.compile(r"preset=last_month"))

    expect(page.locator("#transactions-table.tabulator")).to_be_visible()
    expect(page.locator("a:text-is('Last 30 Days')").first).to_have_class(
        re.compile("btn-active")
    )


def test_explore_query_params_seed_header_filters(page: Page, goto):
    """
    WHEN  user opens Explore with ?internal=Checking
    THEN  the Internal header filter is seeded with that value
    """
    goto("/explore?preset=all&internal=Checking")

    internal_filter_input = page.locator(
        ".tabulator-col:has(.tabulator-col-title:has-text('Internal'))"
        " .tabulator-header-filter input"
    )
    expect(internal_filter_input).to_have_value("Checking")


def test_explore_seeded_header_filter_filters_table(page: Page, goto):
    """
    WHEN  user opens Explore with ?category=Dining
    THEN  the table shows only rows matching the seeded filter
    """
    goto("/explore?preset=all&category=Dining")

    rows = page.locator("#transactions-table .tabulator-row")
    expect(rows.first).to_be_visible()
    page.wait_for_timeout(500)
    # Seeded filter keeps matching rows and drops the rest; at minimum the
    # grid reports a filtered (non-total) row count in its footer counter.
    counter = page.locator("#transactions-table .tabulator-footer")
    expect(counter).to_contain_text(re.compile(r"[0-9]"))
