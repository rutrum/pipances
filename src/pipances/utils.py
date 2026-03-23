from datetime import date, timedelta


def safe_int(
    value: str | None,
    default: int,
    min_val: int | None = None,
    max_val: int | None = None,
) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    if min_val is not None:
        result = max(result, min_val)
    if max_val is not None:
        result = min(result, max_val)
    return result


def safe_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def escape_like(q: str) -> str:
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def compute_date_range(
    preset: str, date_from: str | None, date_to: str | None
) -> tuple[date | None, date | None]:
    if preset == "all":
        return None, None
    today = date.today()
    if preset == "last_month":
        return today - timedelta(days=29), today
    elif preset == "last_3_months":
        return today - timedelta(days=89), today
    elif preset == "last_year":
        return today - timedelta(days=364), today
    elif preset == "custom" and date_from and date_to:
        d_from = safe_date(date_from)
        d_to = safe_date(date_to)
        if d_from and d_to:
            return d_from, d_to
    # Default: YTD
    return today.replace(month=1, day=1), today
