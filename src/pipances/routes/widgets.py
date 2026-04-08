from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from pipances.db import async_session
from pipances.models import Account, Category, Transaction
from pipances.routes._utils import templates
from pipances.utils import escape_like

router = APIRouter()


@router.get("/api/combo/{entity}", response_class=HTMLResponse)
async def combo_search(entity: str, request: Request):
    q = request.query_params.get("q", "").strip()
    txn_id = request.query_params.get("txn_id", "")
    field_name = request.query_params.get("field", "")

    async with async_session() as session:
        if entity == "categories":
            query = select(Category).order_by(Category.name)
            if q:
                query = query.where(
                    Category.name.ilike(f"%{escape_like(q)}%", escape="\\")
                )
            result = await session.execute(query.limit(50))
            items = [{"id": c.id, "name": c.name} for c in result.scalars().all()]
            exact_match = (
                any(item["name"].lower() == q.lower() for item in items) if q else True
            )
        elif entity == "external-accounts":
            query = select(Account).order_by(Account.name)
            if q:
                query = query.where(
                    Account.name.ilike(f"%{escape_like(q)}%", escape="\\")
                )
            result = await session.execute(query.limit(50))
            items = [{"id": a.id, "name": a.name} for a in result.scalars().all()]
            exact_match = (
                any(item["name"].lower() == q.lower() for item in items) if q else True
            )
        elif entity == "descriptions":
            query = (
                select(Transaction.description)
                .where(Transaction.description.isnot(None))
                .where(Transaction.description != "")
                .distinct()
                .order_by(Transaction.description)
            )
            if q:
                query = query.where(
                    Transaction.description.ilike(f"%{escape_like(q)}%", escape="\\")
                )
            result = await session.execute(query.limit(50))
            items = [{"id": 0, "name": d[0]} for d in result.fetchall() if d[0]]
            exact_match = (
                any(item["name"].lower() == q.lower() for item in items) if q else True
            )
        else:
            return HTMLResponse("Unknown entity", status_code=404)

    return templates.TemplateResponse(
        request,
        "_combo_results.html",
        {
            "items": items,
            "query": q,
            "exact_match": exact_match,
            "txn_id": txn_id,
            "field_name": field_name,
            "entity": entity,
        },
    )
