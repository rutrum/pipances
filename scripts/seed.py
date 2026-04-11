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

# === Merchant Variants ===
# Each merchant has multiple realistic raw_description variants (as seen in real bank exports)
# and multiple approved transactions at different amounts to train the model on text, not amount

MERCHANT_VARIANTS = {
    "Kroger": {
        "category": "Groceries",
        "variants": [
            "KROGER #1234",
            "KROGER STORE #1234",
            "KROGER #01234 CITY GA",
            "KRG #1234",
            "KROGER GROCERY #1234",
        ],
        "approved_amounts": [2500, 8700, 14500, 5200, 11300],  # Multiple amounts in cents
    },
    "Whole Foods": {
        "category": "Groceries",
        "variants": [
            "WHOLE FOODS MKT",
            "WHOLE FOODS MARKET",
            "WF MARKET #456",
            "WHOLE FOODS #0456",
            "WHOLE FOODS MKT #456",
        ],
        "approved_amounts": [15000, 4000, 8500, 12000, 6500],
    },
    "Aldi": {
        "category": "Groceries",
        "variants": [
            "ALDI STORE",
            "ALDI #789",
            "ALDI SUPERMARKET",
            "ALDI DISCOUNT",
        ],
        "approved_amounts": [4000, 8000, 5500, 3200],
    },
    "Shell Gas": {
        "category": "Transportation",
        "variants": [
            "SHELL OIL 57432",
            "SHELL GAS STATION",
            "SHELL #57432 GAS",
            "SHELL 57432",
            "SHELL GASOLINE 57432",
        ],
        "approved_amounts": [3500, 5200, 6800, 4100, 5900],
    },
    "BP Gas": {
        "category": "Transportation",
        "variants": [
            "BP GAS STATION",
            "BP #8844",
            "BP GASOLINE",
            "BP FUEL #8844",
        ],
        "approved_amounts": [2800, 4500, 5900, 3200],
    },
    "Chipotle": {
        "category": "Dining",
        "variants": [
            "CHIPOTLE",
            "CHIPOTLE MEXICAN GRL",
            "CHIPOTLE #2156",
            "CHIPOTLE ONLINE",
        ],
        "approved_amounts": [1000, 1500, 800, 1200],
    },
    "Olive Garden": {
        "category": "Dining",
        "variants": [
            "OLIVE GARDEN",
            "OLIVE GARDEN #345",
            "OG RESTAURANT",
            "OLIVE GARDEN ITALIAN",
        ],
        "approved_amounts": [3500, 6000, 4200, 5500],
    },
    "Starbucks": {
        "category": "Dining",
        "variants": [
            "STARBUCKS",
            "STARBUCKS #9012",
            "STARBUCKS COFFEE",
            "SBUX #9012",
        ],
        "approved_amounts": [400, 800, 600, 700],
    },
    "Chick-fil-A": {
        "category": "Dining",
        "variants": [
            "CHICK FIL A",
            "CHICK-FIL-A",
            "CFA #123",
            "CHICK FIL A #123",
        ],
        "approved_amounts": [700, 1400, 900, 1100],
    },
    "Target": {
        "category": "Shopping",
        "variants": [
            "TARGET",
            "TARGET #2847",
            "TARGET STORE #2847",
            "TGT #2847",
            "TARGET RETAIL",
        ],
        "approved_amounts": [3000, 10000, 15000, 8500, 12500],
    },
    "Amazon": {
        "category": "Shopping",
        "variants": [
            "AMAZON.COM",
            "AMZN MKTP US",
            "AMAZON MARKETPLACE",
            "AMAZON.COM MKTP",
            "AMZN PURCHASE",
        ],
        "approved_amounts": [2500, 15000, 8500, 45000, 12000],
    },
    "Home Depot": {
        "category": "Shopping",
        "variants": [
            "HOME DEPOT",
            "HOME DEPOT #5432",
            "HOME DEPOT SUPPLY",
            "HD #5432",
        ],
        "approved_amounts": [4500, 12000, 8900, 15600],
    },
    "Comcast": {
        "category": "Utilities",
        "variants": [
            "COMCAST",
            "COMCAST INTERNET",
            "COMCAST CABLE",
            "COMCAST #999",
        ],
        "approved_amounts": [7999, 7999, 7999],  # Recurring exact amount
    },
    "Electric Company": {
        "category": "Utilities",
        "variants": [
            "ELECTRIC CO",
            "ELECTRIC CO PMT",
            "ELECTRIC UTILITY",
            "CITY ELECTRIC",
        ],
        "approved_amounts": [8500, 14000, 10200, 9800],
    },
    "Water Utility": {
        "category": "Utilities",
        "variants": [
            "WATER UTILITY",
            "CITY WATER",
            "WATER DEPARTMENT",
            "WATER BILL",
        ],
        "approved_amounts": [3500, 5500, 4200, 3800],
    },
    "AMC Theatres": {
        "category": "Entertainment",
        "variants": [
            "AMC THEATRES",
            "AMC THEATRE #123",
            "AMC MOVIES",
            "AMC #123",
        ],
        "approved_amounts": [1500, 2500, 1200, 2000],
    },
    "Netflix": {
        "category": "Entertainment",
        "variants": [
            "NETFLIX",
            "NETFLIX.COM",
            "NETFLIX SUBSCRIPTION",
        ],
        "approved_amounts": [1599, 1599, 1599],  # Recurring exact amount
    },
    "Spotify": {
        "category": "Entertainment",
        "variants": [
            "SPOTIFY",
            "SPOTIFY AB",
            "SPOTIFY PREMIUM",
        ],
        "approved_amounts": [1299, 1299, 1299],  # Recurring exact amount
    },
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

# Recurring transactions
RECURRING_RENT = ("Property Management LLC", "Rent", -140000, "RENT PAYMENT ACH")
RECURRING_PAYCHECK = ("Employer Direct Dep", "Income", 280000, "EMPLOYER DIRECT DEP")


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
        all_external_names = list(MERCHANT_VARIANTS.keys()) + [
            RECURRING_RENT[0],
            RECURRING_PAYCHECK[0],
        ]
        for name in all_external_names:
            if name not in external_map:
                acct = Account(name=name, kind=AccountKind.EXTERNAL)
                session.add(acct)
                await session.flush()
                external_map[name] = acct

        # For transfers, external_map also references internal accounts by name
        for acct in internal_map.values():
            external_map[acct.name] = acct

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
                to_account,
                category_name,
                from_account,
            )
            add_txn(
                txn_date,
                abs(amount_cents),
                raw_desc_to,
                from_account,
                category_name,
                to_account,
            )

        # --- Generate approved transactions with merchant variants ---
        for year, month in MONTHS:
            checking = checking_for_month(year, month)
            savings = savings_for_month(year, month)
            cards = credit_cards_for_month(year, month)

            # --- Recurring: Rent on the 1st ---
            add_txn(
                date(year, month, 1),
                RECURRING_RENT[2],
                RECURRING_RENT[3],
                RECURRING_RENT[0],
                RECURRING_RENT[1],
                checking,
            )

            # --- Recurring: Paychecks on 1st and 15th ---
            for pay_day in [1, 15]:
                add_txn(
                    date(year, month, pay_day),
                    RECURRING_PAYCHECK[2],
                    RECURRING_PAYCHECK[3],
                    RECURRING_PAYCHECK[0],
                    RECURRING_PAYCHECK[1],
                    checking,
                )

            # --- Recurring subscriptions (Netflix, Spotify) ---
            add_txn(
                date(year, month, 12),
                -MERCHANT_VARIANTS["Netflix"]["approved_amounts"][0],
                MERCHANT_VARIANTS["Netflix"]["variants"][0],
                "Netflix",
                MERCHANT_VARIANTS["Netflix"]["category"],
                checking,
            )
            add_txn(
                date(year, month, 18),
                -MERCHANT_VARIANTS["Spotify"]["approved_amounts"][0],
                MERCHANT_VARIANTS["Spotify"]["variants"][0],
                "Spotify",
                MERCHANT_VARIANTS["Spotify"]["category"],
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

            # --- Merchant transactions using variants ---
            # For each merchant, create transactions with variants and different amounts
            for merchant_name, merchant_data in MERCHANT_VARIANTS.items():
                if merchant_name in ["Netflix", "Spotify"]:
                    continue  # Already handled as recurring

                # Pick 2-3 random approved amounts for this month
                num_txns = random.randint(2, 3)
                selected_amounts = random.sample(
                    merchant_data["approved_amounts"],
                    min(num_txns, len(merchant_data["approved_amounts"])),
                )

                for amount in selected_amounts:
                    # Pick a random variant of the raw description
                    raw_desc = random.choice(merchant_data["variants"])
                    internal = random.choice([checking] + (cards if random.random() < 0.3 else []))

                    add_txn(
                        random_date_in_month(year, month),
                        -abs(amount),  # Expenses are negative
                        raw_desc,
                        merchant_name,
                        merchant_data["category"],
                        internal,
                    )

        # Make ~10% uncategorized
        uncategorized_count = 0  # All approved transactions should be categorized
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
                description=txn_data["external_name"],  # Normalized description
                date=txn_data["date"],
                amount_cents=txn_data["amount_cents"],
                status=TransactionStatus.APPROVED,
                category_id=cat.id if cat else None,
            )
            session.add(txn)
            import_counts[imp.institution] = import_counts.get(imp.institution, 0) + 1

        # === Generate pending transactions ===
        pending_transactions = [
            {
                "ext_name": "Kroger",
                "raw_desc": "KROGER STORE #1234",
                "amount": -2350,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 15),
            },
            {
                "ext_name": "Whole Foods",
                "raw_desc": "WHOLE FOODS MARKET",
                "amount": -8900,
                "internal": "Chase Visa",
                "date": date(2026, 9, 16),
            },
            {
                "ext_name": "Shell Gas",
                "raw_desc": "SHELL 57432 GAS",
                "amount": -4500,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 17),
            },
            {
                "ext_name": "Target",
                "raw_desc": "UNKNOWN RETAIL STORE",
                "amount": -3500,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 18),
            },
            {
                "ext_name": "Aldi",
                "raw_desc": "GROCERIES SUPERMARKET",
                "amount": -6200,
                "internal": "Chase Visa",
                "date": date(2026, 9, 19),
            },
            {
                "ext_name": "Starbucks",
                "raw_desc": "STARBUCKS #9012",
                "amount": -12500,
                "internal": "Amex Blue Cash",
                "date": date(2026, 9, 20),
            },
            {
                "ext_name": "Chipotle",
                "raw_desc": "CHPTLE MEX GRL",
                "amount": -1100,
                "internal": "Chase Visa",
                "date": date(2026, 9, 21),
            },
            {
                "ext_name": "Comcast",
                "raw_desc": "COMCAST INTERNET",
                "amount": -7999,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 22),
            },
            {
                "ext_name": "Amazon",
                "raw_desc": "AMZN MKTP US PURCHASE",
                "amount": -19800,
                "internal": "Chase Visa",
                "date": date(2026, 9, 10),
            },
            {
                "ext_name": "Home Depot",
                "raw_desc": "HOME DEPOT #5432",
                "amount": -8500,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 11),
            },
            {
                "ext_name": "BP Gas",
                "raw_desc": "BP GAS STATION #8844",
                "amount": -5900,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 12),
            },
            {
                "ext_name": "Olive Garden",
                "raw_desc": "OLIVE GARDEN ITALIAN",
                "amount": -4200,
                "internal": "Chase Visa",
                "date": date(2026, 9, 13),
            },
            {
                "ext_name": "Chick-fil-A",
                "raw_desc": "CHICK FIL A #123",
                "amount": -900,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 14),
            },
            {
                "ext_name": "Netflix",
                "raw_desc": "NETFLIX SUBSCRIPTION",
                "amount": -1599,
                "internal": "Chase Visa",
                "date": date(2026, 9, 8),
            },
            {
                "ext_name": "Water Utility",
                "raw_desc": "CITY WATER BILL",
                "amount": -4200,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 23),
            },
            {
                "ext_name": "Electric Company",
                "raw_desc": "ELECTRIC CO PMT",
                "amount": -10200,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 24),
            },
            {
                "ext_name": "AMC Theatres",
                "raw_desc": "AMC MOVIES #123",
                "amount": -2000,
                "internal": "Amex Blue Cash",
                "date": date(2026, 9, 25),
            },
            {
                "ext_name": "Whole Foods",
                "raw_desc": "WF MARKET #456",
                "amount": -6500,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 26),
            },
            {
                "ext_name": "Shell Gas",
                "raw_desc": "SHELL GASOLINE 57432",
                "amount": -3500,
                "internal": "Chase Visa",
                "date": date(2026, 9, 27),
            },
            {
                "ext_name": "Target",
                "raw_desc": "TGT #2847",
                "amount": -12500,
                "internal": "Metro CU Checking",
                "date": date(2026, 9, 28),
            },
        ]

        for i, pending_data in enumerate(pending_transactions):
            imp = import_for_account(pending_data["internal"])
            txn = Transaction(
                import_id=imp.id,
                internal_id=internal_map[pending_data["internal"]].id,
                external_id=None,  # Don't set external for pending transactions
                raw_description=pending_data["raw_desc"],
                description=None,
                date=pending_data["date"],
                amount_cents=pending_data["amount"],
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
    pending_count = len(pending_transactions)
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
