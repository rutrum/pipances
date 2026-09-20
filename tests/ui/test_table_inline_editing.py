"""
UI tests for Tabulator inline cell editing on the Data pages.

Focused on the Tom Select cell editor: its arrow-key handling must not leak
through to Tabulator's keybindings module, which would otherwise move the
inline editor to the cell above/below while the user is choosing an option.
"""

from playwright.sync_api import Page, expect


def test_account_type_arrow_keys_change_option_not_row(page: Page, goto):
    """
    WHEN  the user opens the Type (Tom Select) editor on an account row and
          presses ArrowDown
    THEN  Tom Select's active option advances to the next value
    AND   the inline editor stays on the same row (Tabulator does not navigate)
    """
    goto("/data/accounts")

    row = page.locator(".tabulator-row", has_text="Metro CU Checking")
    expect(row).to_be_visible()
    row.locator('.tabulator-cell[tabulator-field="kind"]').click()

    # The editor for this row is open.
    expect(row.locator(".tabulator-cell.tabulator-editing")).to_be_visible()

    # Tom Select renders its dropdown on <body>; the add-account form has a
    # second (hidden) Tom Select, so scope to the visible dropdown.
    active_option = page.locator(".ts-dropdown:visible .option.active")
    expect(active_option).to_have_text("Checking")

    page.keyboard.press("ArrowDown")

    # ArrowDown advanced Tom Select's active option...
    expect(active_option).to_have_text("Savings")
    # ...and the editor did not hop to another row.
    expect(row.locator(".tabulator-cell.tabulator-editing")).to_be_visible()

    # Cancel the edit so nothing is committed. Tom Select consumes the first
    # Escape to close its dropdown, so the second reaches the editor's own
    # Escape handler and cancels the edit.
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    expect(row.locator(".tabulator-cell.tabulator-editing")).not_to_be_visible()
