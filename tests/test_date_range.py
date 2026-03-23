from datetime import date
from unittest.mock import patch

from pipances.utils import compute_date_range


def _freeze(frozen: date):
    """Return a patch context that freezes date.today() to the given date."""
    return patch(
        "pipances.utils.date",
        wraps=date,
        **{"today.return_value": frozen},
    )


def test_preset_all():
    assert compute_date_range("all", None, None) == (None, None)


def test_preset_ytd():
    with _freeze(date(2026, 3, 15)):
        result = compute_date_range("ytd", None, None)
    assert result == (date(2026, 1, 1), date(2026, 3, 15))


def test_preset_last_month():
    with _freeze(date(2026, 3, 15)):
        result = compute_date_range("last_month", None, None)
    assert result == (date(2026, 2, 14), date(2026, 3, 15))


def test_preset_last_month_january():
    with _freeze(date(2026, 1, 10)):
        result = compute_date_range("last_month", None, None)
    assert result == (date(2025, 12, 12), date(2026, 1, 10))


def test_preset_last_3_months():
    with _freeze(date(2026, 3, 15)):
        result = compute_date_range("last_3_months", None, None)
    assert result == (date(2025, 12, 16), date(2026, 3, 15))


def test_preset_last_year():
    with _freeze(date(2026, 3, 15)):
        result = compute_date_range("last_year", None, None)
    assert result == (date(2025, 3, 16), date(2026, 3, 15))


def test_preset_custom_valid():
    result = compute_date_range("custom", "2026-01-01", "2026-02-28")
    assert result == (date(2026, 1, 1), date(2026, 2, 28))


def test_preset_custom_missing_dates():
    with _freeze(date(2026, 3, 15)):
        result = compute_date_range("custom", None, None)
    # Falls through to YTD default
    assert result == (date(2026, 1, 1), date(2026, 3, 15))


def test_unrecognized_preset():
    with _freeze(date(2026, 3, 15)):
        result = compute_date_range("bogus", None, None)
    # Falls through to YTD default
    assert result == (date(2026, 1, 1), date(2026, 3, 15))
