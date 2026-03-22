from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from financial_pipeline.db import async_session
from financial_pipeline.models import (
    Account,
    AccountKind,
    Category,
    Transaction,
)
from financial_pipeline.routes._utils import shared_context, templates
from financial_pipeline.utils import safe_date

router = APIRouter()


@router.get("/settings")
async def settings_redirect():
    return RedirectResponse(url="/settings/accounts")


@router.get("/settings/accounts", response_class=HTMLResponse)
async def settings_accounts_page(request: Request):
    show_closed = request.query_params.get("show_closed", "false") == "true"
    async with async_session() as session:
        shared = await shared_context("settings", session)
        query = (
            select(Account)
            .where(Account.kind != AccountKind.EXTERNAL)
            .order_by(Account.name)
        )
        if not show_closed:
            query = query.where(Account.active == True)
        result = await session.execute(query)
        accounts = result.scalars().all()

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        rows = ""
        for account in accounts:
            rows += templates.get_template("_account_row.html").render(
                {"account": account, "show_closed": show_closed}
            )
        rows += templates.get_template("_account_input_row.html").render()
        return HTMLResponse(rows)

    return templates.TemplateResponse(
        request,
        "settings_accounts.html",
        {
            "accounts": accounts,
            "settings_tab": "accounts",
            "show_closed": show_closed,
            **shared,
        },
    )


@router.post("/settings/accounts", response_class=HTMLResponse)
async def create_account(request: Request):
    form = await request.form()
    name = form.get("name", "").strip()
    kind = form.get("kind", "").strip()
    balance_str = form.get("starting_balance", "").strip()
    balance_date_str = form.get("balance_date", "").strip()

    if not name or not kind:
        return HTMLResponse(
            '<div class="alert alert-error alert-sm">Name and type are required.</div>',
            status_code=422,
        )

    if kind.lower() == AccountKind.EXTERNAL:
        return HTMLResponse(
            '<div class="alert alert-error alert-sm">Account type cannot be "external".</div>',
            status_code=422,
        )

    starting_balance_cents = 0
    if balance_str:
        starting_balance_cents = int(round(float(balance_str) * 100))

    balance_date = safe_date(balance_date_str)

    async with async_session() as session:
        account = Account(
            name=name,
            kind=kind,
            starting_balance_cents=starting_balance_cents,
            balance_date=balance_date,
            active=True,
        )
        session.add(account)
        try:
            await session.commit()
        except IntegrityError:
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">An account with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(account)

    return HTMLResponse(
        templates.get_template("_account_row.html").render({"account": account})
    )


@router.patch("/accounts/{account_id}", response_class=HTMLResponse)
async def update_account(account_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        account = await session.get(Account, account_id)
        if account is None:
            return HTMLResponse("Not found", status_code=404)

        if "name" in form:
            new_name = form["name"].strip()
            if new_name:
                account.name = new_name

        if "kind" in form:
            new_kind = form["kind"].strip()
            if new_kind.lower() == AccountKind.EXTERNAL:
                return HTMLResponse(
                    '<div class="alert alert-error alert-sm">Account type cannot be "external".</div>',
                    status_code=422,
                )
            if new_kind:
                account.kind = new_kind

        if "starting_balance" in form:
            bal = form["starting_balance"].strip()
            if bal:
                account.starting_balance_cents = int(round(float(bal) * 100))
            else:
                account.starting_balance_cents = 0

        if "balance_date" in form:
            bd = form["balance_date"].strip()
            account.balance_date = safe_date(bd)

        if "active" in form:
            account.active = form["active"] == "true"

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">An account with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(account)

    show_closed = request.query_params.get("show_closed", "false") == "true"
    if not account.active and not show_closed:
        return HTMLResponse("")

    return HTMLResponse(
        templates.get_template("_account_row.html").render(
            {"account": account, "show_closed": show_closed}
        )
    )


@router.get("/accounts/{account_id}/edit-name", response_class=HTMLResponse)
async def edit_account_name(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "name",
            "value": account.name,
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-type", response_class=HTMLResponse)
async def edit_account_type(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "kind",
            "value": account.kind,
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-balance", response_class=HTMLResponse)
async def edit_account_balance(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "starting_balance",
            "value": f"{account.starting_balance_cents / 100:.2f}",
            "input_type": "number",
            "step": "0.01",
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/accounts/{account_id}/edit-balance-date", response_class=HTMLResponse)
async def edit_account_balance_date(account_id: int, request: Request):
    async with async_session() as session:
        account = await session.get(Account, account_id)
    if account is None:
        return HTMLResponse("Not found", status_code=404)
    value = str(account.balance_date) if account.balance_date else ""
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "balance_date",
            "value": value,
            "input_type": "date",
            "trigger": "blur, change",
            "endpoint": f"/accounts/{account_id}",
            "target": f"#account-{account_id}",
        },
    )


@router.get("/settings/categories", response_class=HTMLResponse)
async def settings_categories_page(request: Request):
    async with async_session() as session:
        shared = await shared_context("settings", session)
        result = await session.execute(select(Category).order_by(Category.name))
        categories = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "settings_categories.html",
        {
            "categories": categories,
            "settings_tab": "categories",
            **shared,
        },
    )


@router.post("/settings/categories", response_class=HTMLResponse)
async def create_category(request: Request):
    form = await request.form()
    name = form.get("name", "").strip()

    if not name:
        return HTMLResponse(
            '<div class="alert alert-error alert-sm">Name is required.</div>',
            status_code=422,
        )

    async with async_session() as session:
        category = Category(name=name)
        session.add(category)
        try:
            await session.commit()
        except IntegrityError:
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">A category with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(category)

    return HTMLResponse(
        templates.get_template("_category_row.html").render({"category": category})
    )


@router.patch("/categories/{category_id}", response_class=HTMLResponse)
async def update_category(category_id: int, request: Request):
    form = await request.form()
    async with async_session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            return HTMLResponse("Not found", status_code=404)

        if "name" in form:
            new_name = form["name"].strip()
            if new_name:
                category.name = new_name

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return HTMLResponse(
                '<div class="alert alert-error alert-sm">A category with that name already exists.</div>',
                status_code=422,
            )
        await session.refresh(category)

    return HTMLResponse(
        templates.get_template("_category_row.html").render({"category": category})
    )


@router.delete("/categories/{category_id}", response_class=HTMLResponse)
async def delete_category(category_id: int):
    async with async_session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            return HTMLResponse("Not found", status_code=404)

        # Set NULL on transactions referencing this category
        await session.execute(
            Transaction.__table__.update()
            .where(Transaction.category_id == category_id)
            .values(category_id=None)
        )
        await session.delete(category)
        await session.commit()

    return HTMLResponse("")


@router.get("/categories/{category_id}/edit-name", response_class=HTMLResponse)
async def edit_category_name(category_id: int, request: Request):
    async with async_session() as session:
        category = await session.get(Category, category_id)
    if category is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        request,
        "_edit_input.html",
        {
            "field_name": "name",
            "value": category.name,
            "endpoint": f"/categories/{category_id}",
            "target": f"#category-{category_id}",
        },
    )
