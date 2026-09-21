"""Browser tests for the Tabulator inbox range clipboard (phase 4).

The table is remote and rendered client-side, so these tests focus on the one
thing that JSON API tests cannot cover: the custom ``clipboardPasteAction``
turning a real paste into a single batch PATCH.
"""

import sqlite3

import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

DESCRIPTION_CELL = '.tabulator-cell[tabulator-field="description"]'


@pytest.fixture
def pending_txn_ids(ui_db):
    """The first three pending transactions in the table's date-asc order.

    Yields their ids and clears the descriptions again afterwards so later
    tests see a pristine inbox.
    """
    conn = sqlite3.connect(str(ui_db))
    rows = conn.execute(
        "SELECT id FROM transactions WHERE status='pending'"
        " ORDER BY date ASC, id ASC LIMIT 3"
    ).fetchall()
    conn.close()
    if len(rows) < 3:
        pytest.skip("Not enough pending transactions for a range paste test")
    ids = [row[0] for row in rows]
    yield ids

    conn = sqlite3.connect(str(ui_db))
    conn.executemany(
        "UPDATE transactions SET description=NULL WHERE id=?", [(i,) for i in ids]
    )
    conn.commit()
    conn.close()


def _select_description_range(page: Page, start: int, end: int) -> None:
    """Drag-select a vertical range of description cells."""
    cells = page.locator(DESCRIPTION_CELL)
    start_box = cells.nth(start).bounding_box()
    end_box = cells.nth(end).bounding_box()
    assert start_box and end_box
    page.mouse.move(start_box["x"] + 5, start_box["y"] + start_box["height"] / 2)
    page.mouse.down()
    page.mouse.move(end_box["x"] + 5, end_box["y"] + end_box["height"] / 2)
    page.mouse.up()


def _paste(page: Page, text: str):
    """Paste ``text`` into the focused table, preferring the real clipboard.

    Falls back to a synthetic paste event if Chromium refuses the trusted
    clipboard path; both exercise the same custom paste action.
    """
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.evaluate("(text) => navigator.clipboard.writeText(text)", text)
    try:
        with page.expect_response(
            "**/api/inbox/transactions/batch", timeout=3000
        ) as info:
            page.keyboard.press("Control+V")
        return info.value
    except PlaywrightTimeoutError:
        with page.expect_response("**/api/inbox/transactions/batch") as info:
            page.evaluate(
                """(text) => {
                    const table = window.PipancesInboxTable;
                    const dt = new DataTransfer();
                    dt.setData("text/plain", text);
                    table.element.dispatchEvent(new ClipboardEvent("paste", {
                        clipboardData: dt,
                        bubbles: true,
                        cancelable: true,
                    }));
                }""",
                text,
            )
        return info.value


def test_range_paste_persists_across_rows(
    page: Page, goto, live_server, pending_txn_ids
):
    goto("/inbox-tabulator")
    expect(page.locator(DESCRIPTION_CELL).first).to_be_visible()

    _select_description_range(page, 0, 2)
    response = _paste(page, "UI RANGE PASTE")
    assert response.ok

    # The whole range shows the pasted value...
    for index in range(3):
        expect(page.locator(DESCRIPTION_CELL).nth(index)).to_contain_text(
            "UI RANGE PASTE"
        )

    # ...and it survived a reload, i.e. it was persisted by the batch endpoint.
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(page.locator(DESCRIPTION_CELL).first).to_contain_text("UI RANGE PASTE")
