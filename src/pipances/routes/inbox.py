from math import ceil

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import exists as sa_exists
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from pipances.db import async_session
from pipances.models import (
    Account,
    AccountKind,
    Import,
    Transaction,
    TransactionStatus,
)
from pipances.routes._utils import shared_context, templates
from pipances.routes.transactions import SORT_COLUMNS
from pipances.utils import safe_date, safe_int

router = APIRouter()


@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    params = request.query_params
    date_from_str = params.get("date_from", "").strip()
    date_to_str = params.get("date_to", "").strip()
    internal_id = params.get("internal_id", "").strip()
    import_id = params.get("import_id", "").strip()
    sort_col = params.get("sort", "date")
    sort_dir = params.get("dir", "asc")
    page = safe_int(params.get("page"), 1, min_val=1)
    page_size = safe_int(params.get("page_size"), 25, min_val=1, max_val=100)
    internal_id_val = safe_int(internal_id, 0) if internal_id else None
    import_id_val = safe_int(import_id, 0) if import_id else None

    async with async_session() as session:
        query = (
            select(Transaction)
            .where(Transaction.status == TransactionStatus.PENDING)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )

        count_query = (
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.status == TransactionStatus.PENDING)
        )

        date_from = safe_date(date_from_str)
        date_to = safe_date(date_to_str)
        if date_from:
            query = query.where(Transaction.date >= date_from)
            count_query = count_query.where(Transaction.date >= date_from)
        if date_to:
            query = query.where(Transaction.date <= date_to)
            count_query = count_query.where(Transaction.date <= date_to)
        if internal_id_val:
            query = query.where(Transaction.internal_id == internal_id_val)
            count_query = count_query.where(Transaction.internal_id == internal_id_val)
        if import_id_val:
            query = query.where(Transaction.import_id == import_id_val)
            count_query = count_query.where(Transaction.import_id == import_id_val)

        col = SORT_COLUMNS.get(sort_col, Transaction.date)
        if sort_dir == "desc":
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())

        total_count = await session.scalar(count_query)
        total_pages = max(1, ceil(total_count / page_size))
        page = min(page, total_pages)
        offset = (page - 1) * page_size

        result = await session.execute(query.offset(offset).limit(page_size))
        transactions = result.scalars().all()

        # Filter dropdown data
        internal_result = await session.execute(
            select(Account)
            .where(Account.kind != AccountKind.EXTERNAL, Account.active == True)
            .order_by(Account.name)
        )
        internal_accounts = internal_result.scalars().all()

        import_result = await session.execute(
            select(Import).order_by(Import.imported_at.desc())
        )
        imports = import_result.scalars().all()

        shared = await shared_context("inbox", session)

    toast = params.get("toast")
    ctx = {
        "transactions": transactions,
        "internal_accounts": internal_accounts,
        "imports": imports,
        "date_from": date_from_str,
        "date_to": date_to_str,
        "internal_id": internal_id,
        "import_id": import_id,
        "sort": sort_col,
        "dir": sort_dir,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": total_count,
        "toast": toast,
        "import_summary": {
            "imported": params.get("imported"),
            "duplicates": params.get("duplicates"),
            "date_min": params.get("date_min"),
            "date_max": params.get("date_max"),
            "account": params.get("account"),
        }
        if toast == "upload_success"
        else None,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        rows = ""
        for txn in transactions:
            rows += templates.get_template("_inbox_row.html").render({"txn": txn})
        pagination = templates.get_template("_pagination.html").render(
            {
                **ctx,
                "pagination_url": "/inbox",
                "pagination_target": "#inbox-table",
                "pagination_include": "#filter-bar",
                "oob": True,
            }
        )
        pagination_oob = pagination
        thead = templates.get_template("_inbox_thead.html").render(ctx)
        thead_oob = thead.replace(
            '<tr id="inbox-thead">',
            '<tr id="inbox-thead" hx-swap-oob="outerHTML:#inbox-thead">',
            1,
        )
        return HTMLResponse(rows + pagination_oob + thead_oob)

    ctx |= shared
    return templates.TemplateResponse(request, "inbox.html", ctx)


@router.get("/inbox/commit-summary", response_class=HTMLResponse)
async def commit_summary(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(Transaction)
            .where(
                Transaction.status == TransactionStatus.PENDING,
                Transaction.marked_for_approval == True,
            )
            .options(
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
        )
        marked = result.scalars().all()

        if not marked:
            toast = templates.get_template("_toast.html").render(
                {
                    "message": "Nothing to commit -- no transactions are approved.",
                    "type": "warning",
                }
            )
            return HTMLResponse("<!-- empty -->" + toast)

        commit_count = len(marked)

        # Find categories only referenced by pending transactions
        new_category_names = set()
        for txn in marked:
            if txn.category:
                cat_id = txn.category_id
                approved_ref = await session.execute(
                    select(Transaction.id).where(
                        Transaction.category_id == cat_id,
                        Transaction.status == TransactionStatus.APPROVED,
                    )
                )
                if not approved_ref.first():
                    new_category_names.add(txn.category.name)

        # Find external accounts only referenced by pending transactions
        new_external_names = set()
        for txn in marked:
            ext_id = txn.external_id
            approved_ref = await session.execute(
                select(Transaction.id).where(
                    Transaction.external_id == ext_id,
                    Transaction.status == TransactionStatus.APPROVED,
                )
            )
            if not approved_ref.first():
                new_external_names.add(txn.external.name)

    return templates.TemplateResponse(
        request,
        "_commit_summary.html",
        {
            "commit_count": commit_count,
            "new_categories": sorted(new_category_names),
            "new_externals": sorted(new_external_names),
        },
    )


@router.post("/inbox/commit", response_class=HTMLResponse)
async def commit_inbox(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(Transaction).where(
                Transaction.status == TransactionStatus.PENDING,
                Transaction.marked_for_approval == True,
            )
        )
        marked = result.scalars().all()

        if not marked:
            toast = templates.get_template("_toast.html").render(
                {
                    "message": "Nothing to commit -- no transactions are marked.",
                    "type": "warning",
                }
            )
            remaining = await session.execute(
                select(Transaction)
                .where(Transaction.status == TransactionStatus.PENDING)
                .options(
                    selectinload(Transaction.internal),
                    selectinload(Transaction.external),
                    selectinload(Transaction.category),
                )
                .order_by(Transaction.date)
            )
            rows = ""
            for txn in remaining.scalars().all():
                rows += templates.get_template("_inbox_row.html").render({"txn": txn})
            return HTMLResponse(rows + toast)

        committed_count = len(marked)
        for txn in marked:
            txn.status = TransactionStatus.APPROVED
            txn.marked_for_approval = False
        await session.commit()

        # Prune orphaned external accounts
        orphans = (
            (
                await session.execute(
                    select(Account).where(
                        Account.kind == AccountKind.EXTERNAL,
                        ~sa_exists(
                            select(Transaction.id).where(
                                Transaction.external_id == Account.id
                            )
                        ),
                        ~sa_exists(
                            select(Transaction.id).where(
                                Transaction.internal_id == Account.id
                            )
                        ),
                    )
                )
            )
            .scalars()
            .all()
        )
        for orphan in orphans:
            await session.delete(orphan)
        await session.commit()

    # Re-render remaining pending transactions (with filters if present)
    form = await request.form()
    filter_date_from = form.get("date_from", "").strip()
    filter_date_to = form.get("date_to", "").strip()
    filter_internal_id = form.get("internal_id", "").strip()
    filter_import_id = form.get("import_id", "").strip()

    async with async_session() as session:
        query = (
            select(Transaction)
            .where(Transaction.status == TransactionStatus.PENDING)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
            )
            .order_by(Transaction.date)
        )
        d_from = safe_date(filter_date_from)
        if d_from:
            query = query.where(Transaction.date >= d_from)
        d_to = safe_date(filter_date_to)
        if d_to:
            query = query.where(Transaction.date <= d_to)
        int_id = safe_int(filter_internal_id, 0) if filter_internal_id else None
        if int_id:
            query = query.where(Transaction.internal_id == int_id)
        imp_id = safe_int(filter_import_id, 0) if filter_import_id else None
        if imp_id:
            query = query.where(Transaction.import_id == imp_id)

        result = await session.execute(query)
        transactions = result.scalars().all()

        # Count all remaining (unfiltered) for badge
        total_result = await session.execute(
            select(func.count(Transaction.id)).where(
                Transaction.status == TransactionStatus.PENDING
            )
        )
        remaining_count = total_result.scalar() or 0

    # Calculate pagination for remaining transactions
    page_size = 25  # Default page size
    total_pages = (remaining_count + page_size - 1) // page_size

    badge = templates.get_template("_badge.html").render({"count": remaining_count})
    pagination = templates.get_template("_pagination.html").render(
        {
            "page": 1,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_count": remaining_count,
            "pagination_url": "/inbox",
            "pagination_target": "#inbox-table",
            "pagination_include": "#filter-bar",
            "oob": True,
        }
    )
    toast = templates.get_template("_toast.html").render(
        {
            "message": f"Committed {committed_count} transaction{'s' if committed_count != 1 else ''}.",
            "type": "success",
        }
    )
    dialog_clear = '<div id="commit-dialog-container" hx-swap-oob="innerHTML:#commit-dialog-container"></div>'
    oob = toast + badge + pagination + dialog_clear

    if not transactions:
        empty = (
            '<tr><td colspan="6">'
            '<div class="flex flex-col items-center justify-center py-16 text-base-content/60">'
            '<p class="text-xl font-semibold mb-2">All cleaned up!</p>'
            '<p class="mb-4">No pending transactions to review.</p>'
            '<a href="/upload" class="btn btn-primary">Upload transactions</a>'
            "</div></td></tr>"
        )
        return HTMLResponse(empty + oob)

    rows = ""
    for txn in transactions:
        rows += templates.get_template("_inbox_row.html").render({"txn": txn})
    return HTMLResponse(rows + oob)


@router.post("/inbox/retrain", response_class=HTMLResponse)
async def retrain_inbox(request: Request):
    # Extract sort parameters from filter bar
    form_data = await request.form()
    sort_col = form_data.get("sort", "date")
    sort_dir = form_data.get("dir", "asc")

    async with async_session() as session:
        query = (
            select(Transaction)
            .where(Transaction.status == TransactionStatus.PENDING)
            .options(
                selectinload(Transaction.internal),
                selectinload(Transaction.external),
                selectinload(Transaction.category),
                selectinload(Transaction.import_record),
            )
        )

        # Apply sort order from filter bar
        col = SORT_COLUMNS.get(sort_col, Transaction.date)
        if sort_dir == "desc":
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())

        result = await session.execute(query)
        pending = result.scalars().all()

        if not pending:
            toast = templates.get_template("_toast.html").render(
                {"message": "No pending transactions to retrain.", "type": "warning"}
            )
            return HTMLResponse(toast)

        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == TransactionStatus.APPROVED)
            .options(selectinload(Transaction.import_record))
        )
        approved = result.scalars().all()

        if not approved:
            toast = templates.get_template("_toast.html").render(
                {
                    "message": "No training data available. Approve some transactions first.",
                    "type": "warning",
                }
            )
            return HTMLResponse(toast)

        from pipances.predict import TransactionPredictor

        train_raw = [t.raw_description for t in approved]
        train_amounts = [t.amount_cents for t in approved]
        train_dow = [t.date.weekday() for t in approved]
        train_dom = [t.date.day for t in approved]
        train_internal = [str(t.internal_id) for t in approved]
        train_institution = [t.import_record.institution for t in approved]
        train_desc = [t.description for t in approved]
        train_cat = [t.category_id for t in approved]
        train_ext = [t.external_id for t in approved]

        predictor = TransactionPredictor()
        predictor.fit(
            train_raw,
            train_amounts,
            train_dow,
            train_dom,
            train_internal,
            train_institution,
            train_desc,
            train_cat,
            train_ext,
        )

        pred_raw = [t.raw_description for t in pending]
        pred_amounts = [t.amount_cents for t in pending]
        pred_dow = [t.date.weekday() for t in pending]
        pred_dom = [t.date.day for t in pending]
        pred_internal = [str(t.internal_id) for t in pending]
        pred_institution = [t.import_record.institution for t in pending]

        predictions = predictor.predict(
            pred_raw,
            pred_amounts,
            pred_dow,
            pred_dom,
            pred_internal,
            pred_institution,
        )

        updated_count = 0
        for txn, pred in zip(pending, predictions, strict=True):
            if pred.description and (
                txn.ml_confidence_description is None
                or pred.description.confidence > txn.ml_confidence_description
            ):
                txn.description = pred.description.value
                txn.ml_confidence_description = pred.description.confidence
                updated_count += 1
            if pred.category_id and (
                txn.ml_confidence_category is None
                or pred.category_id.confidence > txn.ml_confidence_category
            ):
                txn.category_id = pred.category_id.value
                txn.ml_confidence_category = pred.category_id.confidence
                updated_count += 1
            if pred.external_id and (
                txn.ml_confidence_external is None
                or pred.external_id.confidence > txn.ml_confidence_external
            ):
                txn.external_id = pred.external_id.value
                txn.ml_confidence_external = pred.external_id.confidence
                updated_count += 1

        await session.commit()

        # Refresh relationships so template renders correct data
        for txn in pending:
            await session.refresh(txn, ["category", "external"])

    toast = templates.get_template("_toast.html").render(
        {
            "message": f"Retrained model and updated {updated_count} suggestion{'s' if updated_count != 1 else ''}.",
            "type": "success",
        }
    )

    rows = ""
    for txn in pending:
        rows += templates.get_template("_inbox_row.html").render(
            {"txn": txn, "oob": True}
        )

    return HTMLResponse(rows + toast)
