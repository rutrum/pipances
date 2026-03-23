import html
from urllib.parse import urlencode

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select

from pipances.db import async_session
from pipances.ingest import discover_importers, ingest
from pipances.models import Account, AccountKind
from pipances.routes._utils import shared_context, templates
from pipances.schemas import ImportedTransaction

router = APIRouter()


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    importers = discover_importers()
    async with async_session() as session:
        shared = await shared_context("upload", session)
        result = await session.execute(
            select(Account).where(
                Account.kind != AccountKind.EXTERNAL, Account.active == True
            )
        )
        accounts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "upload.html",
        {
            "importers": importers,
            "accounts": accounts,
            **shared,
        },
    )


@router.post("/upload")
async def upload_file(request: Request):
    form = await request.form()
    importer_key = form.get("importer")
    account = form.get("account")
    file: UploadFile = form.get("file")

    try:
        importers = discover_importers()
        if importer_key not in importers:
            raise ValueError(f"Unknown importer: {importer_key}")

        importer_info = importers[importer_key]
        blob = await file.read()
        df = importer_info.parse(blob)
        df = ImportedTransaction.validate(df)
        result = await ingest(
            df,
            internal_account=account,
            importer_name=importer_info.name,
            filename=file.filename,
        )

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
        safe_msg = html.escape(str(e))
        return HTMLResponse(
            f'<div class="alert alert-error">{safe_msg}</div>',
            status_code=422,
        )
