from math import ceil
from typing import cast

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from pipances.db import DatabaseDep
from pipances.db.accounts import get_active_internal_accounts
from pipances.db.imports import get_imports
from pipances.db.transactions import (
    apply_filters,
    fetch_page,
    pending_txn_count,
    resolve_order,
    txn_options,
)
from pipances.models import (
    Account,
    AccountKind,
    Transaction,
    TransactionStatus,
)
from pipances.routes._utils import shared_context, templates
from pipances.utils import safe_date, safe_int

router = APIRouter()


def _render_inbox_pagination(page: int, page_size: int, total_count: int) -> str:
    """Render inbox pagination with OOB swap attribute."""
    total_pages = max(1, ceil(total_count / page_size))
    return templates.get_template("shared/_pagination.jinja2").render(
        {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_count": total_count,
            "pagination_id": "inbox-pagination",
            "pagination_url": "/inbox",
            "pagination_target": "#inbox-table",
            "pagination_include": "#filter-bar",
            "oob": True,
        }
    )


@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(
    request: Request,
    database: DatabaseDep,
) -> Response:
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

    async with database.session() as session:
        txn_page = await fetch_page(
            session,
            statuses=(TransactionStatus.PENDING,),
            date_from=safe_date(date_from_str),
            date_to=safe_date(date_to_str),
            internal_id=internal_id_val,
            import_id=import_id_val,
            sort_col=sort_col,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        total_count = txn_page.total_count
        total_pages = txn_page.total_pages
        page = txn_page.page
        transactions = txn_page.rows

        # Filter dropdown data
        internal_accounts = await get_active_internal_accounts(session)

        imports = await get_imports(session)

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
            rows += templates.get_template("inbox/_inbox_row.jinja2").render(
                {"txn": txn}
            )
        pagination_oob = _render_inbox_pagination(page, page_size, total_count)
        thead_oob = templates.get_template("inbox/_inbox_thead.jinja2").render(
            {**ctx, "oob": True}
        )
        return HTMLResponse(rows + pagination_oob + thead_oob)

    ctx |= shared
    return templates.TemplateResponse(request, "pages/inbox.jinja2", ctx)


@router.get("/inbox/commit-summary", response_class=HTMLResponse)
async def commit_summary(
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        result = await session.execute(
            select(Transaction)
            .where(
                Transaction.status == TransactionStatus.PENDING,
                Transaction.marked_for_approval == True,
            )
            .options(*txn_options(splits=True))
        )
        marked = result.scalars().all()

        if not marked:
            toast = templates.get_template("shared/_toast.jinja2").render(
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
            cats = []
            if txn.category:
                cats.append(txn.category)
            for split in txn.splits:
                if split.category:
                    cats.append(split.category)
            for cat in cats:
                approved_ref = await session.execute(
                    select(Transaction.id).where(
                        Transaction.category_id == cat.id,
                        Transaction.status == TransactionStatus.APPROVED,
                    )
                )
                if not approved_ref.first():
                    new_category_names.add(cat.name)

        # Find external accounts only referenced by pending transactions
        new_external_names = set()
        for txn in marked:
            if txn.external is None:
                continue
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
        "inbox/_commit_summary.jinja2",
        {
            "commit_count": commit_count,
            "new_categories": sorted(new_category_names),
            "new_externals": sorted(new_external_names),
        },
    )


@router.post("/inbox/commit", response_class=HTMLResponse)
async def commit_inbox(
    request: Request,
    database: DatabaseDep,
) -> Response:
    async with database.session() as session:
        result = await session.execute(
            select(Transaction).where(
                Transaction.status == TransactionStatus.PENDING,
                Transaction.marked_for_approval == True,
            )
        )
        marked = result.scalars().all()

        if not marked:
            toast = templates.get_template("shared/_toast.jinja2").render(
                {
                    "message": "Nothing to commit -- no transactions are marked.",
                    "type": "warning",
                }
            )
            remaining = await session.execute(
                select(Transaction)
                .where(Transaction.status == TransactionStatus.PENDING)
                .options(*txn_options())
                .order_by(Transaction.date)
            )
            rows = ""
            for txn in remaining.scalars().all():
                rows += templates.get_template("inbox/_inbox_row.jinja2").render(
                    {"txn": txn}
                )
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
    filter_date_from = str(form.get("date_from", "")).strip()
    filter_date_to = str(form.get("date_to", "")).strip()
    filter_internal_id = str(form.get("internal_id", "")).strip()
    filter_import_id = str(form.get("import_id", "")).strip()
    page_size = safe_int(str(form.get("page_size")), 25, min_val=1, max_val=100)

    async with database.session() as session:
        rows_result = await session.execute(
            apply_filters(
                select(Transaction)
                .where(Transaction.status == TransactionStatus.PENDING)
                .options(*txn_options())
                .order_by(Transaction.date)
                .limit(page_size),
                date_from=safe_date(filter_date_from),
                date_to=safe_date(filter_date_to),
                internal_id=safe_int(filter_internal_id, 0)
                if filter_internal_id
                else None,
                import_id=safe_int(filter_import_id, 0) if filter_import_id else None,
            )
        )
        transactions = rows_result.scalars().all()

        # Count all remaining (unfiltered) for badge
        remaining_count = await pending_txn_count(session)

    badge = templates.get_template("shared/_badge.jinja2").render(
        {"count": remaining_count}
    )
    pagination = _render_inbox_pagination(1, page_size, remaining_count)
    toast = templates.get_template("shared/_toast.jinja2").render(
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
        rows += templates.get_template("inbox/_inbox_row.jinja2").render({"txn": txn})
    return HTMLResponse(rows + oob)


@router.post("/inbox/retrain", response_class=HTMLResponse)
async def retrain_inbox(
    request: Request,
    database: DatabaseDep,
) -> Response:
    # Extract sort parameters from filter bar
    form_data = await request.form()
    sort_col = form_data.get("sort", "date")
    sort_dir = form_data.get("dir", "asc")

    async with database.session() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == TransactionStatus.PENDING)
            .options(*txn_options(import_record=True))
            .order_by(resolve_order(str(sort_col), str(sort_dir)))
        )
        pending = result.scalars().all()

        if not pending:
            toast = templates.get_template("shared/_toast.jinja2").render(
                {"message": "No pending transactions to retrain.", "type": "warning"}
            )
            return HTMLResponse(toast)

        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == TransactionStatus.APPROVED)
            .options(*txn_options(import_record=True))
        )
        approved = result.scalars().all()

        if not approved:
            toast = templates.get_template("shared/_toast.jinja2").render(
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
            [e for e in train_ext if e is not None],
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
            if (
                pred.description
                and pred.description.value is not None
                and (
                    txn.ml_confidence_description is None
                    or pred.description.confidence > txn.ml_confidence_description
                )
            ):
                txn.description = str(pred.description.value)
                txn.ml_confidence_description = pred.description.confidence
                updated_count += 1
            if (
                pred.category_id
                and pred.category_id.value is not None
                and (
                    txn.ml_confidence_category is None
                    or pred.category_id.confidence > txn.ml_confidence_category
                )
            ):
                txn.category_id = cast(int, pred.category_id.value)
                txn.ml_confidence_category = pred.category_id.confidence
                updated_count += 1
            if (
                pred.external_id
                and pred.external_id.value is not None
                and (
                    txn.ml_confidence_external is None
                    or pred.external_id.confidence > txn.ml_confidence_external
                )
            ):
                txn.external_id = cast(int, pred.external_id.value)
                txn.ml_confidence_external = pred.external_id.confidence
                updated_count += 1

        await session.commit()

        # Refresh relationships so template renders correct data
        for txn in pending:
            await session.refresh(txn, ["category", "external"])

    toast = templates.get_template("shared/_toast.jinja2").render(
        {
            "message": f"Retrained model and updated {updated_count} suggestion{'s' if updated_count != 1 else ''}.",
            "type": "success",
        }
    )

    rows = ""
    for txn in pending:
        rows += templates.get_template("inbox/_inbox_row.jinja2").render(
            {"txn": txn, "oob": True}
        )

    return HTMLResponse(rows + toast)
