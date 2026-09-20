"""JSON API for category tables."""

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from pipances.db import DatabaseDep
from pipances.db.categories import (
    fetch_categories_page,
    transaction_count_for_category,
)
from pipances.models import Category
from pipances.routes.api.queries import tabulator_envelope
from pipances.routes.api.schemas import (
    CategoryRow,
    CategoryUpdate,
    TabulatorRequest,
    TabulatorTableResponse,
)

router = APIRouter(prefix="/api", tags=["categories"])


@router.post(
    "/categories/table",
    response_model=TabulatorTableResponse,
    summary="Categories for Tabulator (remote mode)",
    description=(
        "Tabulator-native endpoint: accepts Tabulator's page/size/sort/filter"
        " body and returns Tabulator's default remote envelope."
        " Used by /data/categories."
    ),
)
async def categories_table(
    payload: TabulatorRequest,
    database: DatabaseDep,
):
    async with database.session() as session:
        page = await fetch_categories_page(
            session,
            sorters=[s.model_dump() for s in payload.sort],
            filters=[f.model_dump() for f in payload.filter],
            page=max(payload.page, 1),
            page_size=min(max(payload.size, 1), 100),
        )
    return tabulator_envelope(
        [
            {"id": row.id, "name": row.name, "txn_count": row.txn_count}
            for row in page.rows
        ],
        page.total_count,
        page.total_pages,
    )


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryRow,
    summary="Update a category",
    description="Rename a category. Returns the updated row including txn_count.",
)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    database: DatabaseDep,
):
    async with database.session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")

        if "name" in payload.model_fields_set:
            name = (payload.name or "").strip()
            if not name:
                raise HTTPException(status_code=422, detail="Name is required")
            category.name = name

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=422,
                detail="A category with that name already exists.",
            ) from None
        await session.refresh(category)
        txn_count = await transaction_count_for_category(session, category.id)

    return {"id": category.id, "name": category.name, "txn_count": txn_count}
