"""
Shared page-helper functions for UI tests.

These are plain functions (not fixtures) that wrap common locator patterns.
Import them directly in test files:

    from tests.ui.helpers import ...
"""

import json

from playwright.sync_api import Page


def create_importer(page: Page, live_server: str, name: str, sql: str) -> dict:
    """Create an importer through the JSON API, bypassing the builder UI.

    Used to set up the edit/delete/duplicate-name tests deterministically
    without exercising the save flow they are not testing. The row is cleaned
    up by the ``importer_cleanup`` fixture.
    """
    response = page.request.post(
        f"{live_server}/api/importers",
        data=json.dumps({"name": name, "sql": sql}),
        headers={"Content-Type": "application/json"},
    )
    assert response.ok, response.text()
    return response.json()
