import html as html_mod
import logging
import os
import tempfile
import time
import uuid
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select

from pipances.db import async_session
from pipances.ingest import (
    discover_importers,
    ingest,
    preview_dedup,
    try_all_importers,
)
from pipances.models import Account, AccountKind, Import, Transaction, TransactionStatus
from pipances.routes._utils import shared_context, templates
from pipances.schemas import ImportedTransaction

logger = logging.getLogger(__name__)

router = APIRouter()

TEMP_DIR = (
    Path(os.environ.get("PIPANCES_TEMP_DIR", tempfile.gettempdir()))
    / "pipances_imports"
)


def _cleanup_stale_temp_files(max_age_seconds: int = 3600) -> None:
    """Delete temp files older than max_age_seconds."""
    if not TEMP_DIR.exists():
        return
    now = time.time()
    for f in TEMP_DIR.glob("import_*.csv"):
        if now - f.stat().st_mtime > max_age_seconds:
            f.unlink(missing_ok=True)


def _save_temp_file(blob: bytes) -> str:
    """Save blob to a temp file, return the token (uuid)."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_temp_files()
    token = uuid.uuid4().hex
    path = TEMP_DIR / f"import_{token}.csv"
    path.write_bytes(blob)
    return token


def _read_temp_file(token: str) -> bytes | None:
    """Read a temp file by token. Returns None if not found."""
    path = TEMP_DIR / f"import_{token}.csv"
    if not path.exists():
        return None
    return path.read_bytes()


def _delete_temp_file(token: str) -> None:
    """Delete a temp file by token."""
    path = TEMP_DIR / f"import_{token}.csv"
    path.unlink(missing_ok=True)


async def _get_active_accounts():
    async with async_session() as session:
        result = await session.execute(
            select(Account).where(
                Account.active == True, Account.kind != AccountKind.EXTERNAL
            )
        )
        return result.scalars().all()


@router.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("import", session)
        result = await session.execute(select(Account).where(Account.active == True))
        accounts = result.scalars().all()
    csv_html = templates.get_template("import/_import_csv.html").render(
        accounts=accounts
    )
    return templates.TemplateResponse(
        request,
        "pages/import.html",
        {
            "import_tab": "csv",
            "import_content_html": csv_html,
            **shared,
        },
    )


@router.get("/import/csv", response_class=HTMLResponse)
async def import_csv_partial(request: Request):
    accounts = await _get_active_accounts()
    return templates.TemplateResponse(
        request,
        "import/_import_csv.html",
        {"accounts": accounts},
    )


@router.get("/import/manual", response_class=HTMLResponse)
async def import_manual_partial(request: Request):
    accounts = await _get_active_accounts()
    return templates.TemplateResponse(
        request,
        "import/_import_manual.html",
        {"accounts": accounts},
    )


@router.get("/import/manual/row", response_class=HTMLResponse)
async def import_manual_row(request: Request):
    return templates.TemplateResponse(request, "import/_import_manual_row.html", {})


@router.post("/import/preview", response_class=HTMLResponse)
async def import_preview(request: Request):
    form = await request.form()
    file: UploadFile = form.get("file")

    if file is None or file.filename == "":
        return HTMLResponse(
            '<div class="alert alert-error">No file selected.</div>',
            status_code=422,
        )

    try:
        blob = await file.read()
        if not blob:
            return HTMLResponse(
                '<div class="alert alert-error">File is empty.</div>',
                status_code=422,
            )

        results = try_all_importers(blob)
        successes = {k: v for k, v in results.items() if v["success"]}
        failures = {k: v for k, v in results.items() if not v["success"]}

        if not successes:
            error_details = "; ".join(
                f"{v['name']}: {html_mod.escape(v['error'])}" for v in failures.values()
            )
            return HTMLResponse(
                f'<div class="alert alert-error">No importers could parse this file. {error_details}</div>',
                status_code=422,
            )

        token = _save_temp_file(blob)
        accounts = await _get_active_accounts()

        # If only one importer matched, auto-select it
        if len(successes) == 1:
            auto_key = next(iter(successes))
            auto_result = successes[auto_key]
            rows = auto_result["df"].to_dicts()
            for row in rows:
                row["amount_cents"] = int(round(row["amount"] * 100))
        else:
            auto_key = None
            rows = None

        return templates.TemplateResponse(
            request,
            "import/_import_preview.html",
            {
                "token": token,
                "successes": successes,
                "failures": failures,
                "auto_importer": auto_key,
                "rows": rows,
                "accounts": accounts,
                "duplicate_flags": None,
                "new_count": len(rows) if rows else 0,
                "dupe_count": 0,
            },
        )
    except Exception as e:
        safe_msg = html_mod.escape(str(e))
        return HTMLResponse(
            f'<div class="alert alert-error">{safe_msg}</div>',
            status_code=422,
        )


@router.post("/import/preview/dedup", response_class=HTMLResponse)
async def import_preview_dedup(request: Request):
    form = await request.form()
    token = form.get("token", "")
    importer_key = form.get("importer", "")
    account_name = form.get("account", "")

    blob = _read_temp_file(token)
    if blob is None:
        return HTMLResponse(
            '<div class="alert alert-error">Preview expired. Please re-upload the file.</div>',
            status_code=422,
        )

    try:
        importers = discover_importers()
        if importer_key not in importers:
            return HTMLResponse(
                f'<div class="alert alert-error">Unknown importer: {html_mod.escape(importer_key)}</div>',
                status_code=422,
            )

        importer_info = importers[importer_key]
        df = importer_info.parse(blob)
        df = ImportedTransaction.validate(df)

        rows = df.to_dicts()
        for row in rows:
            row["amount_cents"] = int(round(row["amount"] * 100))

        if account_name:
            duplicate_flags = await preview_dedup(df, account_name)
            dupe_count = sum(duplicate_flags)
            new_count = len(rows) - dupe_count
        else:
            duplicate_flags = None
            dupe_count = 0
            new_count = len(rows)

        accounts = await _get_active_accounts()

        return templates.TemplateResponse(
            request,
            "import/_import_preview.html",
            {
                "token": token,
                "successes": {importer_key: {"name": importer_info.name}},
                "failures": {},
                "auto_importer": importer_key,
                "rows": rows,
                "accounts": accounts,
                "selected_account": account_name,
                "duplicate_flags": duplicate_flags,
                "new_count": new_count,
                "dupe_count": dupe_count,
            },
        )
    except Exception as e:
        safe_msg = html_mod.escape(str(e))
        return HTMLResponse(
            f'<div class="alert alert-error">{safe_msg}</div>',
            status_code=422,
        )


@router.post("/import/commit")
async def import_commit(request: Request):
    form = await request.form()
    token = form.get("token", "")
    importer_key = form.get("importer", "")
    account_name = form.get("account", "")

    if not token or not importer_key or not account_name:
        return HTMLResponse(
            '<div class="alert alert-error">Missing required fields.</div>',
            status_code=422,
        )

    blob = _read_temp_file(token)
    if blob is None:
        return HTMLResponse(
            '<div class="alert alert-error">Preview expired. Please re-upload the file.</div>',
            status_code=422,
        )

    try:
        importers = discover_importers()
        if importer_key not in importers:
            return HTMLResponse(
                f'<div class="alert alert-error">Unknown importer: {html_mod.escape(importer_key)}</div>',
                status_code=422,
            )

        importer_info = importers[importer_key]
        df = importer_info.parse(blob)
        df = ImportedTransaction.validate(df)

        result = await ingest(
            df,
            internal_account=account_name,
            importer_name=importer_info.name,
            filename=f"import_{token}.csv",
        )

        _delete_temp_file(token)

        params = urlencode(
            {
                "toast": "upload_success",
                "imported": result.inserted_count,
                "duplicates": result.duplicate_count,
                "date_min": str(result.date_min) if result.date_min else "",
                "date_max": str(result.date_max) if result.date_max else "",
                "account": result.internal_account_name,
            }
        )
        return Response(status_code=200, headers={"HX-Redirect": f"/inbox?{params}"})
    except Exception as e:
        safe_msg = html_mod.escape(str(e))
        return HTMLResponse(
            f'<div class="alert alert-error">{safe_msg}</div>',
            status_code=422,
        )


@router.post("/import/manual")
async def import_manual_submit(request: Request):
    form = await request.form()
    account_name = form.get("account", "")

    if not account_name:
        return HTMLResponse(
            '<div class="alert alert-error">Please select an account.</div>',
            status_code=422,
        )

    # Collect rows from the spreadsheet form
    dates = form.getlist("date[]")
    amounts = form.getlist("amount[]")
    descriptions = form.getlist("description[]")

    valid_rows = []
    for d, a, desc in zip(dates, amounts, descriptions, strict=False):
        d = d.strip()
        a = a.strip()
        desc = desc.strip()
        if not d and not a and not desc:
            continue
        if not d or not a or not desc:
            return HTMLResponse(
                '<div class="alert alert-error">Each row must have date, amount, and description filled in (or be completely empty).</div>',
                status_code=422,
            )
        try:
            parsed_date = date.fromisoformat(d)
        except ValueError:
            return HTMLResponse(
                f'<div class="alert alert-error">Invalid date: {html_mod.escape(d)}</div>',
                status_code=422,
            )
        try:
            amount_cents = int(round(float(a) * 100))
        except ValueError:
            return HTMLResponse(
                f'<div class="alert alert-error">Invalid amount: {html_mod.escape(a)}</div>',
                status_code=422,
            )
        valid_rows.append(
            {"date": parsed_date, "amount_cents": amount_cents, "description": desc}
        )

    if not valid_rows:
        return HTMLResponse(
            '<div class="alert alert-error">No transactions provided.</div>',
            status_code=422,
        )

    try:
        async with async_session() as session:
            internal = await session.scalar(
                select(Account).where(Account.name == account_name)
            )
            if internal is None:
                return HTMLResponse(
                    f'<div class="alert alert-error">Account {html_mod.escape(account_name)!r} not found.</div>',
                    status_code=422,
                )

            import_record = Import(
                institution="Manual",
                filename=None,
                row_count=len(valid_rows),
            )
            session.add(import_record)
            await session.flush()

            new_txn_ids = []
            all_dates = []
            for row in valid_rows:
                # Resolve or create external account from description
                ext = await session.scalar(
                    select(Account).where(Account.name == row["description"])
                )
                if ext is None:
                    ext = Account(name=row["description"], kind=AccountKind.EXTERNAL)
                    session.add(ext)
                    await session.flush()

                txn = Transaction(
                    import_id=import_record.id,
                    internal_id=internal.id,
                    external_id=ext.id,
                    raw_description=row["description"],
                    description=row["description"],
                    date=row["date"],
                    amount_cents=row["amount_cents"],
                    status=TransactionStatus.PENDING,
                )
                session.add(txn)
                await session.flush()
                new_txn_ids.append(txn.id)
                all_dates.append(row["date"])

            await session.commit()

        # Run ML predictions on newly inserted transactions
        if new_txn_ids:
            from pipances.ingest import _predict_for_transactions

            await _predict_for_transactions(new_txn_ids)

        date_min = min(all_dates) if all_dates else None
        date_max = max(all_dates) if all_dates else None
        params = urlencode(
            {
                "toast": "upload_success",
                "imported": len(valid_rows),
                "duplicates": 0,
                "date_min": str(date_min) if date_min else "",
                "date_max": str(date_max) if date_max else "",
                "account": account_name,
            }
        )
        return Response(status_code=200, headers={"HX-Redirect": f"/inbox?{params}"})
    except Exception as e:
        safe_msg = html_mod.escape(str(e))
        return HTMLResponse(
            f'<div class="alert alert-error">{safe_msg}</div>',
            status_code=422,
        )
