import importlib.util
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import patito as pt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from financial_pipeline.db import async_session
from financial_pipeline.models import Account, Import, Transaction
from financial_pipeline.schemas import ImportedTransaction

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMPORTERS_DIR = PROJECT_ROOT / "importers"


@dataclass
class ImporterInfo:
    name: str
    module_name: str
    parse: Callable[[bytes], pt.DataFrame[ImportedTransaction]]


def discover_importers() -> dict[str, ImporterInfo]:
    importers: dict[str, ImporterInfo] = {}

    if not IMPORTERS_DIR.is_dir():
        return importers

    for path in sorted(IMPORTERS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue

        module_name = path.stem
        spec = importlib.util.spec_from_file_location(f"importers.{module_name}", path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "IMPORTER_NAME"):
            raise ValueError(f"Importer {path} missing IMPORTER_NAME")
        if not hasattr(module, "parse"):
            raise ValueError(f"Importer {path} missing parse() function")

        importers[module_name] = ImporterInfo(
            name=module.IMPORTER_NAME,
            module_name=module_name,
            parse=module.parse,
        )

    return importers


async def _resolve_account(
    session: AsyncSession, name: str, kind: str = "external"
) -> Account:
    account = await session.scalar(select(Account).where(Account.name == name))
    if account is None:
        account = Account(name=name, kind=kind)
        session.add(account)
        await session.flush()
    return account


async def ingest(
    df: pt.DataFrame[ImportedTransaction],
    internal_account: str,
    importer_name: str,
    filename: str | None = None,
) -> int:
    """Ingest a validated ImportedTransaction DataFrame into the database.

    Returns the number of transactions written.
    """
    ImportedTransaction.validate(df)

    async with async_session() as session:
        internal = await session.scalar(
            select(Account).where(Account.name == internal_account)
        )
        if internal is None:
            raise ValueError(f"Internal account {internal_account!r} not found")

        import_record = Import(
            institution=importer_name,
            filename=filename,
            row_count=len(df),
        )
        session.add(import_record)
        await session.flush()

        for row in df.to_dicts():
            external = await _resolve_account(session, row["description"])

            amount_cents = int(row["amount"] * 100)

            txn = Transaction(
                import_id=import_record.id,
                internal_id=internal.id,
                external_id=external.id,
                raw_description=row["description"],
                description=None,
                date=row["date"],
                amount_cents=amount_cents,
                status="pending",
            )
            session.add(txn)

        await session.commit()

    return len(df)
