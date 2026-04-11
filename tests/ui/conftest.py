"""
UI test fixtures: live uvicorn server + seeded database.

The server runs on port 8099 against a temp DB file isolated from the dev DB.
Each test session gets one seed; tests that mutate state should be marked
with @pytest.mark.usefixtures("reset_db") or use their own transactions carefully.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UI_TEST_PORT = 8099
BASE_URL = f"http://localhost:{UI_TEST_PORT}"


# === Override unit-test fixtures that must not bleed into UI tests ===


@pytest.fixture(autouse=True)
def patch_db():
    """No-op: UI tests run against a real seeded server; DB patching is not needed."""
    return


# === Browser configuration ===


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """On NixOS, Playwright's bundled Chromium lacks system libs.
    Use the system Chromium (available in the nix develop shell) instead."""
    chromium_path = shutil.which("chromium") or shutil.which("google-chrome-stable")
    if chromium_path:
        return {**browser_type_launch_args, "executable_path": chromium_path}
    return browser_type_launch_args


# === Server lifecycle ===


@pytest.fixture(scope="session")
def ui_db(tmp_path_factory):
    """Create an isolated DB file and seed it once for the whole test session."""
    db_file = tmp_path_factory.mktemp("ui_db") / "test_pipances.db"
    env = {**os.environ, "PIPANCES_DB_PATH": str(db_file)}
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "seed.py")],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Seed failed:\n{result.stdout}\n{result.stderr}")
    return db_file


@pytest.fixture(scope="session")
def live_server(ui_db):
    """Start uvicorn on port 8099 using the seeded test DB. Killed after session."""
    env = {
        **os.environ,
        "PIPANCES_DB_PATH": str(ui_db),
        "PIPANCES_STATIC_DIR": str(PROJECT_ROOT / "static"),
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "pipances.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(UI_TEST_PORT),
        ],
        env=env,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for server to be ready
    deadline = time.time() + 15
    import urllib.request

    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/inbox", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    else:
        proc.kill()
        raise RuntimeError(f"Server on port {UI_TEST_PORT} never became ready")
    yield BASE_URL
    proc.kill()
    proc.wait()


# === Page helpers ===


@pytest.fixture
def goto(page: Page, live_server):
    """Helper: navigate to a path relative to the live server."""

    def _goto(path: str, **kwargs):
        page.goto(f"{live_server}{path}", **kwargs)
        page.wait_for_load_state("networkidle")

    return _goto


@pytest.fixture
def approvable_txn(ui_db):
    """
    Set description on one pending transaction so its Approve button is enabled.
    Yields the transaction ID. Restores the transaction fully after the test,
    even if it was committed during the test.
    """
    conn = sqlite3.connect(str(ui_db))
    row = conn.execute(
        "SELECT id FROM transactions WHERE status='pending' LIMIT 1"
    ).fetchone()
    if row is None:
        conn.close()
        pytest.skip("No pending transactions available for this test")
    txn_id = row[0]
    conn.execute(
        "UPDATE transactions SET description='Test Transaction' WHERE id=?",
        (txn_id,),
    )
    conn.commit()
    conn.close()

    yield txn_id

    # Restore: reset description, marked_for_approval, and status to pending
    conn = sqlite3.connect(str(ui_db))
    conn.execute(
        "UPDATE transactions SET description=NULL, marked_for_approval=0, status='pending' WHERE id=?",
        (txn_id,),
    )
    conn.commit()
    conn.close()


# === Re-export commonly used playwright assertions ===
# Tests can import `expect` from here instead of playwright directly.
__all__ = ["expect"]
