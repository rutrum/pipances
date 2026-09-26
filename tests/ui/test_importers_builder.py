"""
End-to-end browser tests for the SQL importer pages.

The builder is pure JS over the JSON /api (no HTMX), so server-rendered route
tests cannot reach it. These tests drive the real pages on the live server and
cover the frozen browser contract (interface section 7): the Tabulator list,
the staged builder (sample first, then editor + preview), Run against an
uploaded sample, Save (navigating back to the list with a toast), and the
parse/query/validate error surfaces.

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

# A working query over the inferred `raw` relation: the contract requires
# date/amount/description, so cast each explicitly.
WORKING_SQL = """\
SELECT
  CAST(date AS DATE) AS date,
  CAST(amount AS DECIMAL(38,2)) AS amount,
  CAST(description AS VARCHAR) AS description
FROM raw
"""


def _pick_sample(page: Page) -> None:
    """Select the sample CSV and wait for the staged editor + raw grid."""
    page.locator("#importer-file").set_input_files(str(SAMPLE_CSV))
    expect(page.locator("#importer-editor")).to_be_visible()
    expect(page.locator("#importer-preview table")).to_be_visible()


def _run(page: Page) -> None:
    with page.expect_response("**/api/importers/preview") as info:
        page.locator("#importer-run").click()
    assert info.value.ok


def test_importers_page_loads_and_table_renders(page: Page, goto):
    """
    WHEN  user opens /data/importers
    THEN  the Tabulator list mounts with its columns and the New link to the
          dedicated builder page
    """
    goto("/data/importers")

    expect(page.locator("#importers-table.tabulator")).to_be_visible()
    for title in ("Name", "Updated"):
        expect(
            page.locator(".tabulator-col-title", has_text=title).first
        ).to_be_visible()
    new_link = page.locator("#importer-new")
    expect(new_link).to_be_visible()
    expect(new_link).to_have_attribute("href", "/data/importers/new")


def test_builder_hides_editor_until_sample_chosen(page: Page, goto):
    """
    WHEN  the user opens /data/importers/new
    THEN  only Name and Sample CSV show; the SQL editor is hidden until a
          sample is picked, then prefilled with SELECT * FROM raw
    """
    goto("/data/importers/new")

    expect(page.locator("#importer-name")).to_be_visible()
    expect(page.locator("#importer-file")).to_be_visible()
    expect(page.locator("#importer-editor")).to_be_hidden()
    expect(page.locator("#importer-sql")).to_be_hidden()

    _pick_sample(page)

    expect(page.locator("#importer-sql")).to_be_visible()
    expect(page.locator("#importer-sql")).to_have_value("SELECT * FROM raw")
    # test_export.csv infers the contract columns, so the default query already
    # validates and renders its full result grid with no warning.
    expect(page.locator("#importer-preview table")).to_contain_text("SPOTIFY PREMIUM")
    expect(page.locator("#importer-summary")).to_contain_text("11 rows validated")
    expect(page.locator("#importer-error")).to_be_empty()


def test_run_renders_validated_preview(page: Page, goto):
    """
    WHEN  the user runs a working SELECT
    THEN  the raw VARCHAR schema, the result grid, and the validation summary
          all render on the page
    """
    goto("/data/importers/new")
    _pick_sample(page)

    page.locator("#importer-sql").fill(WORKING_SQL)
    _run(page)

    raw_schema = page.locator("#importer-raw-schema")
    expect(raw_schema).to_contain_text("VARCHAR")

    rows = page.locator("#importer-preview tbody tr")
    expect(rows).to_have_count(11)
    expect(rows.first).to_contain_text("2025-12-18")
    expect(rows.first).to_contain_text("-12.99")
    expect(rows.first).to_contain_text("SPOTIFY PREMIUM")

    expect(page.locator("#importer-summary")).to_contain_text("11 rows validated")
    expect(page.locator("#importer-error")).to_be_empty()


def test_parse_error_keeps_last_grid_marked_stale(page: Page, goto):
    """
    WHEN  a good preview is followed by a SQL parse error
    THEN  the last good grid stays visible and is tinted stale
    """
    goto("/data/importers/new")
    _pick_sample(page)

    page.locator("#importer-sql").fill(WORKING_SQL)
    _run(page)
    expect(page.locator("#importer-summary")).to_contain_text("11 rows validated")

    page.locator("#importer-sql").fill("SELECT 1; DROP TABLE x")
    _run(page)

    expect(page.locator("#importer-error")).to_contain_text("parse")
    # Never blank the last good table; tint it instead.
    grid = page.locator("#importer-preview")
    expect(grid.locator("table")).to_be_visible()
    expect(grid.locator("tbody tr").first).to_contain_text("SPOTIFY PREMIUM")
    expect(grid).to_have_class(re.compile("border-warning"))


def test_validate_error_replaces_grid_with_warning(page: Page, goto):
    """
    WHEN  a good preview is followed by SQL that executes but fails the contract
    THEN  the executed grid replaces the old one and a soft warning shows, with
          no stale tint
    """
    goto("/data/importers/new")
    _pick_sample(page)

    page.locator("#importer-sql").fill(WORKING_SQL)
    _run(page)
    expect(page.locator("#importer-summary")).to_contain_text("11 rows validated")

    page.locator("#importer-sql").fill("SELECT date, description FROM raw")
    _run(page)

    expect(page.locator("#importer-error")).to_contain_text("validate")
    expect(page.locator("#importer-error .alert-warning")).to_be_visible()
    expect(page.locator("#importer-preview table")).to_be_visible()
    expect(page.locator("#importer-preview")).not_to_have_class(
        re.compile("border-warning")
    )


def test_save_validates_then_navigates_with_toast(page: Page, goto):
    """
    WHEN  the user saves a new importer
    THEN  Save validates first, then persists, navigates to the list, and shows
          a toast
    """
    goto("/data/importers/new")
    _pick_sample(page)

    page.locator("#importer-name").fill("UI Saved Importer")
    page.locator("#importer-sql").fill(WORKING_SQL)

    with page.expect_response("**/api/importers/preview") as preview_info:
        with page.expect_response("**/api/importers") as save_info:
            page.locator("#importer-save").click()
    assert preview_info.value.ok
    assert save_info.value.status == 201

    expect(page).to_have_url(re.compile(r"/data/importers\?toast=importer_saved$"))
    expect(
        page.locator("#importers-table .tabulator-row", has_text="UI Saved Importer")
    ).to_be_visible()
    expect(page.locator("#toast-container .alert")).to_contain_text("Importer saved")


def test_draft_save_without_sample_navigates_with_warning(page: Page, goto):
    """
    WHEN  the user saves without a sample or a successful Run (decision 9)
    THEN  the importer is still created and a draft warning toast shows
    """
    goto("/data/importers/new")

    page.locator("#importer-name").fill("UI Draft Importer")

    with page.expect_response("**/api/importers") as info:
        page.locator("#importer-save").click()
    assert info.value.status == 201

    expect(page).to_have_url(re.compile(r"/data/importers\?toast=importer_draft$"))
    expect(page.locator("#toast-container .alert")).to_contain_text("draft")


def test_run_without_sample_reports_error(page: Page, goto):
    """
    WHEN  the user clicks Run before picking a sample
    THEN  an error is shown and the editor stays hidden
    """
    goto("/data/importers/new")

    page.locator("#importer-run").click()

    expect(page.locator("#importer-error")).to_contain_text(
        "Pick a sample CSV before running."
    )
    expect(page.locator("#importer-editor")).to_be_hidden()


def test_list_edit_link_opens_prefilled_builder(page: Page, goto, live_server):
    """
    WHEN  the user follows the row Edit action
    THEN  the edit builder opens with name prefilled and, after a fresh sample
          is picked, the saved SQL with its validated preview
    """
    importer = create_importer(page, live_server, "UI Edit Importer", WORKING_SQL)
    goto("/data/importers")

    row = page.locator("#importers-table .tabulator-row", has_text="UI Edit Importer")
    expect(row).to_be_visible()
    edit_path = f"/data/importers/{importer['id']}/edit"
    row.locator(f'a[href="{edit_path}"]').click()
    page.wait_for_load_state("networkidle")

    expect(page).to_have_url(re.compile(rf"/data/importers/{importer['id']}/edit$"))
    expect(page.locator("#importer-name")).to_have_value("UI Edit Importer")
    # Samples are never persisted (decision 8): the editor stays hidden until a
    # sample is re-picked.
    expect(page.locator("#importer-editor")).to_be_hidden()
    assert page.eval_on_selector("#importer-file", "el => el.files.length") == 0

    _pick_sample(page)
    expect(page.locator("#importer-sql")).to_have_value(WORKING_SQL)
    expect(page.locator("#importer-summary")).to_contain_text("11 rows validated")


def test_edit_page_prefills_name_and_sql(page: Page, goto, live_server):
    """
    WHEN  the user opens /data/importers/{id}/edit directly
    THEN  name and SQL are embedded from the server
    """
    importer = create_importer(page, live_server, "UI Direct Edit", WORKING_SQL)
    goto(f"/data/importers/{importer['id']}/edit")

    expect(page.locator("#importer-name")).to_have_value("UI Direct Edit")
    expect(page.locator("#importer-sql")).to_have_value(WORKING_SQL)


def test_duplicate_name_shows_409_without_navigating(page: Page, goto, live_server):
    """
    WHEN  the user saves an importer whose name already exists
    THEN  the 409 detail is shown inline and the builder stays open
    """
    create_importer(page, live_server, "UI Duplicate Importer", WORKING_SQL)
    goto("/data/importers/new")
    _pick_sample(page)

    page.locator("#importer-name").fill("UI Duplicate Importer")
    page.locator("#importer-sql").fill(WORKING_SQL)

    with page.expect_response("**/api/importers/preview"):
        with page.expect_response("**/api/importers") as info:
            page.locator("#importer-save").click()
    assert info.value.status == 409

    expect(page.locator("#importer-error")).to_contain_text("already exists")
    expect(page).to_have_url(re.compile(r"/data/importers/new$"))


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
