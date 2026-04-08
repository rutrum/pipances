"""Seed the database with deterministic test data.

Generates 12 months of transactions (Oct 2025 - Sep 2026) across:
- Two banks (First National closes Feb 2026, Metro CU opens Feb 2026)
- Two credit cards (Chase Visa full year, Amex Blue Cash from Dec 2025)
- Paired transfers (savings<->checking, checking<->credit cards, bank switchover)
"""

import asyncio
import random
from datetime import date, timedelta

from pipances.db import async_session, create_tables
from pipances.models import (
    Account,
    AccountKind,
    Category,
    Import,
    Transaction,
    TransactionStatus,
)

random.seed(42)

# === Internal Accounts ===

INTERNAL_ACCOUNTS = [
    # First National (active Oct 2025 - Jan 2026, closed Feb 2026)
    {
        "name": "FN Checking",
        "kind": "checking",
        "starting_balance_cents": 450000,
        "balance_date": date(2025, 9, 30),
        "active": False,
    },
    {
        "name": "FN Savings",
        "kind": "savings",
        "starting_balance_cents": 1200000,
        "balance_date": date(2025, 9, 30),
        "active": False,
    },
    # Metro Credit Union (opens Feb 2026)
    {
        "name": "Metro CU Checking",
        "kind": "checking",
        "starting_balance_cents": 0,
        "balance_date": date(2026, 1, 31),
        "active": True,
    },
    {
        "name": "Metro CU Savings",
        "kind": "savings",
        "starting_balance_cents": 0,
        "balance_date": date(2026, 1, 31),
        "active": True,
    },
    # Credit cards (full year / from Dec 2025)
    {
        "name": "Chase Visa",
        "kind": "credit_card",
        "starting_balance_cents": -32500,
        "balance_date": date(2025, 9, 30),
        "active": True,
    },
    {
        "name": "Amex Blue Cash",
        "kind": "credit_card",
        "starting_balance_cents": 0,
        "balance_date": date(2025, 11, 30),
        "active": True,
    },
]

# === Categories ===

CATEGORY_NAMES = [
    "Groceries",
    "Dining",
    "Entertainment",
    "Utilities",
    "Rent",
    "Transportation",
    "Shopping",
    "Income",
    "Credit Card Payment",
    "Savings Transfer",
    "Bank Migration",
]

# === External Accounts (merchants/payees) with typical category and amount range ===

MERCHANTS = [
    ("Kroger", "Groceries", -12000, -3000),
    ("Whole Foods", "Groceries", -15000, -4000),
    ("Aldi", "Groceries", -8000, -2000),
    ("Chipotle", "Dining", -1500, -800),
    ("Olive Garden", "Dining", -6000, -2500),
    ("Starbucks", "Dining", -800, -400),
    ("Chick-fil-A", "Dining", -1400, -700),
    ("AMC Theatres", "Entertainment", -2500, -1200),
    ("Barnes & Noble", "Entertainment", -4000, -1000),
    ("Shell Gas Station", "Transportation", -6500, -3000),
    ("BP Gas Station", "Transportation", -5500, -2800),
    ("Target", "Shopping", -10000, -2000),
    ("Amazon", "Shopping", -15000, -1500),
    ("Home Depot", "Shopping", -12000, -2500),
    ("Comcast Internet", "Utilities", -7999, -7999),
    ("Electric Company", "Utilities", -14000, -8500),
    ("Water Utility", "Utilities", -5500, -3500),
]

# Recurring items
RECURRING = {
    "rent": ("Property Management LLC", "Rent", -140000),
    "paycheck": ("Employer Direct Dep", "Income", 280000),
    "netflix": ("Netflix", "Entertainment", -1599),
    "spotify": ("Spotify", "Entertainment", -1299),
}

# 12 months: Oct 2025 through Sep 2026
MONTHS = [
    (2025, 10),
    (2025, 11),
    (2025, 12),
    (2026, 1),
    (2026, 2),
    (2026, 3),
    (2026, 4),
    (2026, 5),
    (2026, 6),
    (2026, 7),
    (2026, 8),
    (2026, 9),
]

# Bank switchover happens in Feb 2026
SWITCHOVER_MONTH = (2026, 2)


def random_date_in_month(year: int, month: int) -> date:
    if month == 12:
        last_day = (date(year + 1, 1, 1) - timedelta(days=1)).day
    else:
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
    day = random.randint(1, last_day)
    return date(year, month, day)


def checking_for_month(year: int, month: int) -> str:
    """Return the active checking account name for a given month."""
    if (year, month) < SWITCHOVER_MONTH:
        return "FN Checking"
    return "Metro CU Checking"


def savings_for_month(year: int, month: int) -> str:
    """Return the active savings account name for a given month."""
    if (year, month) < SWITCHOVER_MONTH:
        return "FN Savings"
    return "Metro CU Savings"


def credit_cards_for_month(year: int, month: int) -> list[str]:
    """Return available credit cards for a given month."""
    cards = ["Chase Visa"]
    if (year, month) >= (2025, 12):
        cards.append("Amex Blue Cash")
    return cards


async def seed():
    await create_tables()

    async with async_session() as session:
        # === Create internal accounts ===
        internal_map: dict[str, Account] = {}
        for acct_data in INTERNAL_ACCOUNTS:
            acct = Account(**acct_data)
            session.add(acct)
            await session.flush()
            internal_map[acct.name] = acct

        # === Create categories ===
        category_map: dict[str, Category] = {}
        for name in CATEGORY_NAMES:
            cat = Category(name=name)
            session.add(cat)
            await session.flush()
            category_map[name] = cat

        # === Create external accounts ===
        external_map: dict[str, Account] = {}
        all_external_names = (
            [m[0] for m in MERCHANTS]
            + [v[0] for v in RECURRING.values()]
        )
        for name in all_external_names:
            if name not in external_map:
                acct = Account(name=name, kind=AccountKind.EXTERNAL)
                session.add(acct)
                await session.flush()
                external_map[name] = acct

        # === Create import records (one per institution) ===
        import_fn = Import(institution="First National", filename="seed.py", row_count=0)
        import_metro = Import(institution="Metro Credit Union", filename="seed.py", row_count=0)
        import_chase = Import(institution="Chase", filename="seed.py", row_count=0)
        import_amex = Import(institution="Amex", filename="seed.py", row_count=0)
        for imp in [import_fn, import_metro, import_chase, import_amex]:
            session.add(imp)
        await session.flush()

        def import_for_account(acct_name: str) -> Import:
            if acct_name.startswith("FN"):
                return import_fn
            if acct_name.startswith("Metro"):
                return import_metro
            if acct_name.startswith("Chase"):
                return import_chase
            if acct_name.startswith("Amex"):
                return import_amex
            return import_fn

        # === Generate approved transactions ===
        transactions: list[dict] = []

        def add_txn(
            txn_date: date,
            amount_cents: int,
            raw_description: str,
            external_name: str,
            category_name: str | None,
            internal: str,
        ):
            transactions.append(
                {
                    "date": txn_date,
                    "amount_cents": amount_cents,
                    "raw_description": raw_description,
                    "external_name": external_name,
                    "category_name": category_name,
                    "internal": internal,
                }
            )

        def add_transfer_pair(
            txn_date: date,
            amount_cents: int,
            raw_desc_from: str,
            raw_desc_to: str,
            from_account: str,
            to_account: str,
            category_name: str,
        ):
            """Add both sides of a transfer. Both internal_id and external_id reference the same account."""
            add_txn(
                txn_date,
                -abs(amount_cents),
                raw_desc_from,
                to_account,  # Just the account name - same as internal account
                category_name,
                from_account,
            )
            add_txn(
                txn_date,
                abs(amount_cents),
                raw_desc_to,
                from_account,  # Just the account name - same as internal account
                category_name,
                to_account,
            )

        for year, month in MONTHS:
            checking = checking_for_month(year, month)
            savings = savings_for_month(year, month)
            cards = credit_cards_for_month(year, month)

            # --- Recurring: Rent on the 1st ---
            add_txn(
                date(year, month, 1),
                RECURRING["rent"][2],
                "RENT PAYMENT ACH",
                RECURRING["rent"][0],
                RECURRING["rent"][1],
                checking,
            )

            # --- Recurring: Paychecks on 1st and 15th ---
            for pay_day in [1, 15]:
                add_txn(
                    date(year, month, pay_day),
                    RECURRING["paycheck"][2],
                    "EMPLOYER DIRECT DEP",
                    RECURRING["paycheck"][0],
                    RECURRING["paycheck"][1],
                    checking,
                )

            # --- Recurring: Netflix (12th) ---
            add_txn(
                date(year, month, 12),
                RECURRING["netflix"][2],
                "NETFLIX SUBSCRIPTION",
                RECURRING["netflix"][0],
                RECURRING["netflix"][1],
                checking,
            )

            # --- Recurring: Spotify (18th) ---
            add_txn(
                date(year, month, 18),
                RECURRING["spotify"][2],
                "SPOTIFY PREMIUM",
                RECURRING["spotify"][0],
                RECURRING["spotify"][1],
                checking,
            )

            # --- Transfer: Savings to Checking (25th) ---
            add_transfer_pair(
                date(year, month, 25),
                50000,
                "TRANSFER TO CHECKING",
                "TRANSFER FROM SAVINGS",
                savings,
                checking,
                "Savings Transfer",
            )

            # --- Transfer: Checking to Chase Visa payment (5th) ---
            chase_payment = random.randint(30000, 80000)
            add_transfer_pair(
                date(year, month, 5),
                chase_payment,
                "CHASE VISA PAYMENT",
                "PAYMENT RECEIVED",
                checking,
                "Chase Visa",
                "Credit Card Payment",
            )

            # --- Transfer: Checking to Amex payment (8th, from Jan 2026) ---
            if (year, month) >= (2026, 1):
                amex_payment = random.randint(15000, 45000)
                add_transfer_pair(
                    date(year, month, 8),
                    amex_payment,
                    "AMEX PAYMENT",
                    "PAYMENT RECEIVED",
                    checking,
                    "Amex Blue Cash",
                    "Credit Card Payment",
                )

            # --- Bank switchover transfers (Feb 2026) ---
            if (year, month) == SWITCHOVER_MONTH:
                add_transfer_pair(
                    date(2026, 2, 3),
                    350000,
                    "ACH TRANSFER TO METRO CU",
                    "ACH TRANSFER FROM FIRST NATIONAL",
                    "FN Checking",
                    "Metro CU Checking",
                    "Bank Migration",
                )
                add_transfer_pair(
                    date(2026, 2, 3),
                    1100000,
                    "ACH TRANSFER TO METRO CU",
                    "ACH TRANSFER FROM FIRST NATIONAL",
                    "FN Savings",
                    "Metro CU Savings",
                    "Bank Migration",
                )

            # --- Random merchant transactions (8-12 per month) ---
            num_random = random.randint(8, 12)
            for _ in range(num_random):
                merchant_name, cat_name, min_amt, max_amt = random.choice(MERCHANTS)
                amount = random.randint(min_amt, max_amt)
                # Pick payment method: credit card ~40%, checking ~60%
                if random.random() < 0.4 and cards:
                    internal = random.choice(cards)
                else:
                    internal = checking
                add_txn(
                    random_date_in_month(year, month),
                    amount,
                    merchant_name.upper(),
                    merchant_name,
                    cat_name,
                    internal,
                )

        # Make ~10% uncategorized
        uncategorized_count = len(transactions) // 10
        uncategorized_indices = random.sample(range(len(transactions)), uncategorized_count)
        for idx in uncategorized_indices:
            transactions[idx]["category_name"] = None

        # Insert approved transactions
        import_counts: dict[str, int] = {}
        for txn_data in transactions:
            cat = (
                category_map.get(txn_data["category_name"])
                if txn_data["category_name"]
                else None
            )
            imp = import_for_account(txn_data["internal"])
            txn = Transaction(
                import_id=imp.id,
                internal_id=internal_map[txn_data["internal"]].id,
                external_id=external_map[txn_data["external_name"]].id,
                raw_description=txn_data["raw_description"],
                description=None,
                date=txn_data["date"],
                amount_cents=txn_data["amount_cents"],
                status=TransactionStatus.APPROVED,
                category_id=cat.id if cat else None,
            )
            session.add(txn)
            import_counts[imp.institution] = import_counts.get(imp.institution, 0) + 1

        # === Generate pending transactions (inbox) ===
        pending_merchants = [
            ("Kroger", "KROGER #1234", -8743, "Metro CU Checking"),
            ("Whole Foods", "WHOLE FOODS MKT", -6521, "Chase Visa"),
            ("Shell Gas Station", "SHELL OIL 57432", -4899, "Metro CU Checking"),
            ("Amazon", "AMZN MKTP US", -3299, "Amex Blue Cash"),
            ("Chipotle", "CHIPOTLE ONLINE", -1247, "Chase Visa"),
            ("Electric Company", "ELECTRIC CO PMT", -11200, "Metro CU Checking"),
            ("Starbucks", "STARBUCKS #9012", -575, "Amex Blue Cash"),
            ("Target", "TARGET T-2847", -5432, "Metro CU Checking"),
        ]

        for i, (ext_name, raw_desc, amount, internal_name) in enumerate(pending_merchants):
            imp = import_for_account(internal_name)
            txn = Transaction(
                import_id=imp.id,
                internal_id=internal_map[internal_name].id,
                external_id=external_map[ext_name].id,
                raw_description=raw_desc,
                description=None,
                date=date(2026, 9, 15 + i),
                amount_cents=amount,
                status=TransactionStatus.PENDING,
            )
            session.add(txn)
            import_counts[imp.institution] = import_counts.get(imp.institution, 0) + 1

        # Update import record row counts
        import_fn.row_count = import_counts.get("First National", 0)
        import_metro.row_count = import_counts.get("Metro Credit Union", 0)
        import_chase.row_count = import_counts.get("Chase", 0)
        import_amex.row_count = import_counts.get("Amex", 0)

        await session.commit()

    approved_count = len(transactions)
    pending_count = len(pending_merchants)
    print(f"Seeded {approved_count} approved + {pending_count} pending transactions")
    print(f"  {len(INTERNAL_ACCOUNTS)} internal accounts")
    print(f"  {len(external_map)} external accounts")
    print(f"  {len(CATEGORY_NAMES)} categories")
    print(f"  4 import records (FN, Metro CU, Chase, Amex)")
    print(f"  {uncategorized_count} transactions left uncategorized")
    for inst, count in sorted(import_counts.items()):
        print(f"  {inst}: {count} transactions")


if __name__ == "__main__":
    asyncio.run(seed())
