"""
End-to-end browser tests for the SQL importer builder (/data/importers).

The builder is pure JS over the JSON /api (no HTMX), so server-rendered route
tests cannot reach it. These tests drive the real page on the live server and
cover the frozen browser contract (interface section 7): the Tabulator list, the
New/Edit modal with the read-only server preamble, Run against an uploaded
sample, Save in place, and the parse/query/409 error surfaces.

Every importer created here is removed by `importer_cleanup` via the
module-level `usefixtures`, so the session-scoped seed DB is left as found.
"""

import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from tests.ui.helpers import create_importer

pytestmark = pytest.mark.usefixtures("importer_cleanup")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV = PROJECT_ROOT / "test_export.csv"
PREAMBLE = "SELECT * FROM read_csv('input_file.csv', all_varchar = true)"
PREAMBLE_LOCATOR = 'textarea[aria-label="Server-owned preamble, illustrative only"]'

# A working query over the all-VARCHAR `raw` relation: the contract requires
# date/amount/description, so cast each explicitly.
WORKING_SQL = """\
SELECT
  CAST(date AS DATE) AS date,
  CAST(amount AS DECIMAL(38,2)) AS amount,
  CAST(description AS VARCHAR) AS description
FROM raw
"""


def _open_new_builder(page: Page) -> None:
    page.locator("#importer-new").click()
    expect(page.locator("#importer-modal")).to_be_visible()


def test_importers_page_loads_and_table_renders(page: Page, goto):
    """
    WHEN  user opens /data/importers
    THEN  the Tabulator list mounts with its columns and the New button
    """
    goto("/data/importers")

    expect(page.locator("#importers-table.tabulator")).to_be_visible()
    for title in ("Name", "Updated"):
        expect(
            page.locator(".tabulator-col-title", has_text=title).first
        ).to_be_visible()
    expect(page.locator("#importer-new")).to_be_visible()


def test_new_importer_opens_builder_with_readonly_preamble(page: Page, goto):
    """
    WHEN  the user clicks New Importer
    THEN  the builder dialog opens with a disabled, read-only preamble
    """
    goto("/data/importers")
    _open_new_builder(page)

    expect(page.locator("#importer-modal-title")).to_have_text("New Importer")

    preamble = page.locator(PREAMBLE_LOCATOR)
    expect(preamble).to_be_disabled()
    expect(preamble).to_have_attribute("readonly", "")
    expect(preamble).to_have_value(PREAMBLE)


def test_run_renders_raw_schema_and_transformed_preview(page: Page, goto):
    """
    WHEN  the user uploads test_export.csv and runs a working SELECT
    THEN  the raw VARCHAR schema, the transformed rows, and the validation
          summary all render in the dialog
    """
    goto("/data/importers")
    _open_new_builder(page)

    page.locator("#importer-file").set_input_files(str(SAMPLE_CSV))
    page.locator("#importer-sql").fill(WORKING_SQL)

    with page.expect_response("**/api/importers/preview") as info:
        page.locator("#importer-run").click()
    assert info.value.ok

    raw_schema = page.locator("#importer-raw-schema")
    expect(raw_schema).to_contain_text("date")
    expect(raw_schema).to_contain_text("amount")
    expect(raw_schema).to_contain_text("description")
    # all_varchar: every raw column is sniffed as VARCHAR.
    expect(raw_schema).to_contain_text("VARCHAR")

    rows = page.locator("#importer-preview tbody tr")
    expect(rows).to_have_count(11)
    expect(rows.first).to_contain_text("2025-12-18")
    expect(rows.first).to_contain_text("-12.99")
    expect(rows.first).to_contain_text("SPOTIFY PREMIUM")

    expect(page.locator("#importer-summary")).to_contain_text("11 rows validated")


def test_save_adds_row_in_place_and_closes_dialog(page: Page, goto):
    """
    WHEN  the user saves a new importer
    THEN  a row appears in the list without navigation and the dialog closes
    """
    goto("/data/importers")
    _open_new_builder(page)

    page.locator("#importer-name").fill("UI Saved Importer")
    page.locator("#importer-sql").fill(WORKING_SQL)

    with page.expect_response("**/api/importers") as info:
        page.locator("#importer-save").click()
    assert info.value.status == 201

    expect(page.locator("#importer-modal")).not_to_be_visible()
    expect(page).to_have_url(re.compile(r"/data/importers$"))
    expect(
        page.locator("#importers-table .tabulator-row", has_text="UI Saved Importer")
    ).to_be_visible()


def test_edit_prefills_and_requires_a_fresh_sample(page: Page, goto, live_server):
    """
    WHEN  the user opens a saved importer for editing and clicks Run
    THEN  name and SQL are prefilled, the file input is cleared, and Run warns
          that a sample must be re-picked
    """
    create_importer(page, live_server, "UI Edit Importer", WORKING_SQL)
    goto("/data/importers")

    row = page.locator("#importers-table .tabulator-row", has_text="UI Edit Importer")
    expect(row).to_be_visible()
    row.locator('button[data-action="edit"]').click()

    expect(page.locator("#importer-modal")).to_be_visible()
    expect(page.locator("#importer-modal-title")).to_have_text("Edit Importer")
    expect(page.locator("#importer-name")).to_have_value("UI Edit Importer")
    expect(page.locator("#importer-sql")).to_have_value(WORKING_SQL)
    # Samples are never persisted: the file input must start empty.
    assert page.eval_on_selector("#importer-file", "el => el.files.length") == 0

    page.locator("#importer-run").click()
    expect(page.locator("#importer-error")).to_contain_text(
        "Pick a sample CSV before running."
    )
    expect(page.locator("#importer-modal")).to_be_visible()


def test_bad_sql_reports_parse_stage(page: Page, goto):
    """
    WHEN  the user runs multi-statement SQL
    THEN  the dialog shows a parse-stage error and stays open
    """
    goto("/data/importers")
    _open_new_builder(page)

    page.locator("#importer-file").set_input_files(str(SAMPLE_CSV))
    page.locator("#importer-sql").fill("SELECT 1; DROP TABLE x")

    with page.expect_response("**/api/importers/preview") as info:
        page.locator("#importer-run").click()
    assert info.value.ok

    error_box = page.locator("#importer-error")
    expect(error_box).to_contain_text("parse")
    expect(error_box).to_contain_text("single SELECT")
    expect(page.locator("#importer-modal")).to_be_visible()


def test_bad_sql_reports_query_stage_for_unknown_column(page: Page, goto):
    """
    WHEN  the user runs a SELECT over a column that does not exist
    THEN  the dialog shows a query-stage error
    """
    goto("/data/importers")
    _open_new_builder(page)

    page.locator("#importer-file").set_input_files(str(SAMPLE_CSV))
    page.locator("#importer-sql").fill(
        "SELECT"
        " CAST(nope AS DATE) AS date,"
        " CAST(amount AS DECIMAL(38,2)) AS amount,"
        " CAST(description AS VARCHAR) AS description"
        " FROM raw"
    )

    with page.expect_response("**/api/importers/preview") as info:
        page.locator("#importer-run").click()
    assert info.value.ok

    error_box = page.locator("#importer-error")
    expect(error_box).to_contain_text("query")
    expect(page.locator("#importer-modal")).to_be_visible()


def test_duplicate_name_shows_409_without_closing(page: Page, goto, live_server):
    """
    WHEN  the user saves an importer whose name already exists
    THEN  the 409 detail is shown in the dialog and the dialog stays open
    """
    create_importer(page, live_server, "UI Duplicate Importer", WORKING_SQL)
    goto("/data/importers")
    _open_new_builder(page)

    page.locator("#importer-name").fill("UI Duplicate Importer")
    page.locator("#importer-sql").fill(WORKING_SQL)

    with page.expect_response("**/api/importers") as info:
        page.locator("#importer-save").click()
    assert info.value.status == 409

    expect(page.locator("#importer-error")).to_contain_text("already exists")
    expect(page.locator("#importer-modal")).to_be_visible()


def test_delete_removes_row(page: Page, goto, live_server):
    """
    WHEN  the user deletes an importer from the list
    THEN  its row disappears and the DELETE returns 204
    """
    create_importer(page, live_server, "UI Delete Importer", WORKING_SQL)
    goto("/data/importers")

    row = page.locator("#importers-table .tabulator-row", has_text="UI Delete Importer")
    expect(row).to_be_visible()

    with page.expect_response(re.compile(r"/api/importers/\d+")) as info:
        row.locator('button[data-action="delete"]').click()
    assert info.value.status == 204

    expect(
        page.locator("#importers-table .tabulator-row", has_text="UI Delete Importer")
    ).to_have_count(0)
