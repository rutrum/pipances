"""Seed the database with deterministic test data."""

import asyncio
import random
from datetime import date, timedelta

from financial_pipeline.db import async_session, create_tables
from financial_pipeline.models import Account, AccountKind, Category, Import, Transaction, TransactionStatus

random.seed(42)

# === Internal Accounts ===

INTERNAL_ACCOUNTS = [
    {"name": "Checking", "kind": "checking", "starting_balance_cents": 450000, "balance_date": date(2025, 9, 30)},
    {"name": "Savings", "kind": "savings", "starting_balance_cents": 1200000, "balance_date": date(2025, 9, 30)},
    {"name": "Credit Card", "kind": "credit_card", "starting_balance_cents": -32500, "balance_date": date(2025, 9, 30)},
]

# === Categories ===

CATEGORY_NAMES = [
    "Groceries", "Dining", "Entertainment", "Utilities",
    "Rent", "Transportation", "Shopping", "Income", "Transfers",
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

# Recurring items (handled separately)
RECURRING = {
    "rent": ("Property Management LLC", "Rent", -140000),
    "paycheck": ("Employer Direct Dep", "Income", 280000),
    "netflix": ("Netflix", "Entertainment", -1599),
    "spotify": ("Spotify", "Entertainment", -1299),
    "transfer": ("Transfer to Savings", "Transfers", -50000),
}

# Months to generate: Oct 2025 through Mar 2026
MONTHS = [
    (2025, 10), (2025, 11), (2025, 12),
    (2026, 1), (2026, 2), (2026, 3),
]


def random_date_in_month(year: int, month: int) -> date:
    if month == 12:
        last_day = (date(year + 1, 1, 1) - timedelta(days=1)).day
    else:
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
    day = random.randint(1, last_day)
    return date(year, month, day)


async def seed():
    await create_tables()

    async with async_session() as session:
        # === Create internal accounts ===
        internal_map = {}
        for acct_data in INTERNAL_ACCOUNTS:
            acct = Account(**acct_data, active=True)
            session.add(acct)
            await session.flush()
            internal_map[acct.name] = acct

        # === Create categories ===
        category_map = {}
        for name in CATEGORY_NAMES:
            cat = Category(name=name)
            session.add(cat)
            await session.flush()
            category_map[name] = cat

        # === Create external accounts ===
        external_map = {}
        all_external_names = [m[0] for m in MERCHANTS] + [v[0] for v in RECURRING.values()]
        for name in all_external_names:
            if name not in external_map:
                acct = Account(name=name, kind=AccountKind.EXTERNAL)
                session.add(acct)
                await session.flush()
                external_map[name] = acct

        # === Create import record ===
        import_record = Import(
            institution="seed",
            filename="seed.py",
            row_count=0,
        )
        session.add(import_record)
        await session.flush()

        # === Generate approved transactions ===
        transactions = []

        for year, month in MONTHS:
            # Rent on the 1st
            transactions.append({
                "date": date(year, month, 1),
                "amount_cents": RECURRING["rent"][2],
                "raw_description": "RENT PAYMENT ACH",
                "external_name": RECURRING["rent"][0],
                "category_name": RECURRING["rent"][1],
                "internal": "Checking",
            })

            # Paychecks on 1st and 15th
            for pay_day in [1, 15]:
                transactions.append({
                    "date": date(year, month, pay_day),
                    "amount_cents": RECURRING["paycheck"][2],
                    "raw_description": "EMPLOYER DIRECT DEP",
                    "external_name": RECURRING["paycheck"][0],
                    "category_name": RECURRING["paycheck"][1],
                    "internal": "Checking",
                })

            # Netflix (mid-month)
            transactions.append({
                "date": date(year, month, 12),
                "amount_cents": RECURRING["netflix"][2],
                "raw_description": "NETFLIX SUBSCRIPTION",
                "external_name": RECURRING["netflix"][0],
                "category_name": RECURRING["netflix"][1],
                "internal": "Checking",
            })

            # Spotify (mid-month)
            transactions.append({
                "date": date(year, month, 18),
                "amount_cents": RECURRING["spotify"][2],
                "raw_description": "SPOTIFY PREMIUM",
                "external_name": RECURRING["spotify"][0],
                "category_name": RECURRING["spotify"][1],
                "internal": "Checking",
            })

            # Transfer to savings (end of month)
            transactions.append({
                "date": date(year, month, 25),
                "amount_cents": RECURRING["transfer"][2],
                "raw_description": "TRANSFER TO SAVINGS",
                "external_name": RECURRING["transfer"][0],
                "category_name": RECURRING["transfer"][1],
                "internal": "Checking",
            })

            # Random merchant transactions (6-8 per month)
            num_random = random.randint(6, 8)
            for _ in range(num_random):
                merchant_name, cat_name, min_amt, max_amt = random.choice(MERCHANTS)
                amount = random.randint(min_amt, max_amt)
                # Use credit card ~40% of the time for expenses
                internal = "Credit Card" if random.random() < 0.4 else "Checking"
                transactions.append({
                    "date": random_date_in_month(year, month),
                    "amount_cents": amount,
                    "raw_description": merchant_name.upper(),
                    "external_name": merchant_name,
                    "category_name": cat_name,
                    "internal": internal,
                })

        # Make ~10% uncategorized
        uncategorized_count = len(transactions) // 10
        uncategorized_indices = random.sample(range(len(transactions)), uncategorized_count)
        for idx in uncategorized_indices:
            transactions[idx]["category_name"] = None

        # Insert approved transactions
        for txn_data in transactions:
            cat = category_map.get(txn_data["category_name"]) if txn_data["category_name"] else None
            txn = Transaction(
                import_id=import_record.id,
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

        # === Generate pending transactions (inbox) ===
        pending_merchants = [
            ("Kroger", "KROGER #1234", -8743, "Checking"),
            ("Whole Foods", "WHOLE FOODS MKT", -6521, "Credit Card"),
            ("Shell Gas Station", "SHELL OIL 57432", -4899, "Checking"),
            ("Amazon", "AMZN MKTP US", -3299, "Credit Card"),
            ("Chipotle", "CHIPOTLE ONLINE", -1247, "Credit Card"),
            ("Electric Company", "ELECTRIC CO PMT", -11200, "Checking"),
            ("Starbucks", "STARBUCKS #9012", -575, "Credit Card"),
            ("Target", "TARGET T-2847", -5432, "Checking"),
        ]

        for i, (ext_name, raw_desc, amount, internal_name) in enumerate(pending_merchants):
            txn = Transaction(
                import_id=import_record.id,
                internal_id=internal_map[internal_name].id,
                external_id=external_map[ext_name].id,
                raw_description=raw_desc,
                description=None,
                date=date(2026, 3, 15 + i),
                amount_cents=amount,
                status=TransactionStatus.PENDING,
            )
            session.add(txn)

        # Update import record row count
        import_record.row_count = len(transactions) + len(pending_merchants)

        await session.commit()

    approved_count = len(transactions)
    pending_count = len(pending_merchants)
    print(f"Seeded {approved_count} approved + {pending_count} pending transactions")
    print(f"  {len(INTERNAL_ACCOUNTS)} internal accounts")
    print(f"  {len(external_map)} external accounts")
    print(f"  {len(CATEGORY_NAMES)} categories")
    print(f"  {uncategorized_count} transactions left uncategorized")


if __name__ == "__main__":
    asyncio.run(seed())
