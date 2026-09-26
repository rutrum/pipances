"""JSON API for DB-backed SQL importers.

CRUD over the ``importers`` table plus a stateless DuckDB preview. The preview
receives the sample CSV in memory, runs the user's SQL against it, and returns
the raw schema, a display slice of the transformed rows, and any error. Nothing
here touches the filesystem importers (the Python discovery path is Phase 2).
"""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError

from pipances.db import DatabaseDep
from pipances.db.importers import (
    create_importer as db_create_importer,
)
from pipances.db.importers import (
    delete_importer as db_delete_importer,
)
from pipances.db.importers import (
    list_importers as db_list_importers,
)
from pipances.db.importers import (
    update_importer as db_update_importer,
)
from pipances.duckdb_transform import PreviewResult, preview_importer
from pipances.models import Importer
from pipances.routes.api.schemas import (
    ImporterCreate,
    ImporterItem,
    ImporterPreviewError,
    ImporterPreviewResponse,
    ImporterUpdate,
    RawColumnItem,
)
from pipances.settings import settings

router = APIRouter(prefix="/api", tags=["importers"])


def _importer_to_item(importer: Importer) -> ImporterItem:
    return ImporterItem(
        id=importer.id,
        name=importer.name,
        sql=importer.sql,
        created_at=importer.created_at.isoformat(),
        updated_at=importer.updated_at.isoformat(),
    )


def _preview_to_response(result: PreviewResult) -> ImporterPreviewResponse:
    error = (
        None
        if result.error is None
        else ImporterPreviewError(
            stage=result.error.stage, message=result.error.message
        )
    )
    return ImporterPreviewResponse(
        raw_columns=[
            RawColumnItem(name=c.name, type=c.type) for c in result.raw_columns
        ],
        raw_rows=result.raw_rows,
        rows=result.rows,
        total_rows=result.total_rows,
        truncated=result.truncated,
        error=error,
        result_columns=[
            RawColumnItem(name=c.name, type=c.type) for c in result.result_columns
        ],
        result_rows=result.result_rows,
    )


@router.get(
    "/importers",
    response_model=list[ImporterItem],
    summary="List SQL importers",
    description=(
        "Return every saved SQL importer (id, name, sql, timestamps)."
        " Used by /data/importers."
    ),
)
async def list_importers(database: DatabaseDep) -> list[ImporterItem]:
    async with database.session() as session:
        importers = await db_list_importers(session)
    return [_importer_to_item(importer) for importer in importers]


@router.post(
    "/importers",
    response_model=ImporterItem,
    status_code=201,
    summary="Create a SQL importer",
    description="Create an importer from a name and DuckDB SELECT statement.",
)
async def create_importer(
    payload: ImporterCreate,
    database: DatabaseDep,
) -> ImporterItem:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")

    async with database.session() as session:
        try:
            importer = await db_create_importer(session, name=name, sql=payload.sql)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail="An importer with that name already exists.",
            ) from None
        await session.refresh(importer)
    return _importer_to_item(importer)


@router.patch(
    "/importers/{importer_id}",
    response_model=ImporterItem,
    summary="Update a SQL importer",
    description="Rename an importer and/or replace its SQL.",
)
async def update_importer(
    importer_id: int,
    payload: ImporterUpdate,
    database: DatabaseDep,
) -> ImporterItem:
    fields = payload.model_fields_set
    name: str | None = None
    if "name" in fields:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Name is required")

    async with database.session() as session:
        try:
            importer = await db_update_importer(
                session,
                importer_id,
                name=name,
                sql=payload.sql if "sql" in fields else None,
            )
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail="An importer with that name already exists.",
            ) from None
        if importer is None:
            raise HTTPException(status_code=404, detail="Importer not found")
        await session.commit()
        await session.refresh(importer)
    return _importer_to_item(importer)


@router.delete(
    "/importers/{importer_id}",
    status_code=204,
    summary="Delete a SQL importer",
    description="Remove a saved importer. Returns 404 when it does not exist.",
)
async def delete_importer(importer_id: int, database: DatabaseDep) -> None:
    async with database.session() as session:
        deleted = await db_delete_importer(session, importer_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Importer not found")
        await session.commit()


@router.post(
    "/importers/preview",
    response_model=ImporterPreviewResponse,
    summary="Preview a SQL importer against a sample",
    description=(
        "Run the given SQL against the uploaded CSV sample in memory."
        " Always returns 200; parse/query/validate failures are embedded in"
        " the `error` field. Writes nothing to disk."
    ),
)
async def preview(
    file: Annotated[UploadFile, File()],
    sql: Annotated[str, Form()],
) -> ImporterPreviewResponse:
    blob = await file.read()
    if len(blob) > settings.importer_upload_max_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")
    if len(sql) > settings.importer_sql_max_length:
        raise HTTPException(status_code=422, detail="SQL is too long")

    result = await asyncio.to_thread(preview_importer, sql, blob)
    return _preview_to_response(result)
