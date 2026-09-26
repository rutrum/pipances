from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import polars as pl
import pytest

from pipances import duckdb_transform
from pipances.duckdb_transform import (
    ImporterSqlError,
    RawColumn,
    assert_single_select,
    load_raw,
    preview_importer,
    run_importer_sql,
    run_importers_sql,
)
from pipances.settings import settings

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORT_CSV = (REPO_ROOT / "test_export.csv").read_bytes()
METRO_CSV = (REPO_ROOT / "test_metro_cu.csv").read_bytes()

EXAMPLE_SQL = """
SELECT
  CAST(date AS DATE) AS date,
  CAST(amount AS DECIMAL(38,2)) AS amount,
  CAST(description AS VARCHAR) AS description
FROM raw
"""

METRO_SQL = """
SELECT
  CAST(strptime("Transaction Date", '%m/%d/%Y') AS DATE) AS date,
  CASE
    WHEN "Credit" IS NOT NULL THEN CAST("Credit" AS DECIMAL(38,2))
    ELSE -CAST("Debit" AS DECIMAL(38,2))
  END AS amount,
  CAST("Memo" AS VARCHAR) AS description
FROM raw
"""

# Semicolon-delimited variant of the Metro shape.
SEMICOLON_CSV = (
    b"Transaction Date;Debit;Credit;Memo\n"
    b"02/15/2026;;2800.00;EMPLOYER DIRECT DEP\n"
    b"02/16/2026;87.43;;KROGER #1234\n"
)

# Simple export with preamble junk before the real header.
PREAMBLE_CSV = (
    b"Account Export\n"
    b"Generated 2026-03-01\n"
    b"Date,Amount,Description\n"
    b"2026-01-15,19.99,Coffee\n"
    b"2026-01-16,-5.00,Tea\n"
)


def _open_con():
    return duckdb_transform._connect()


# ---------------------------------------------------------------------------
# Repo fixtures
# ---------------------------------------------------------------------------


def test_example_csv_roundtrip():
    df = run_importer_sql(EXAMPLE_SQL, EXPORT_CSV)
    assert df.height == 11
    assert df.schema["date"] == pl.Date
    assert df.schema["amount"] == pl.Decimal(38, 2)
    assert df.schema["description"] == pl.String
    first = df.row(0, named=True)
    assert first["date"].isoformat() == "2025-12-18"
    assert first["amount"] == Decimal("-12.99")
    assert first["description"] == "SPOTIFY PREMIUM"


def test_metro_cu_split_debit_credit():
    df = run_importer_sql(METRO_SQL, METRO_CSV)
    assert df.height == 25
    rows = df.to_dicts()
    # Debits become negative, credits stay positive.
    assert rows[0]["amount"] == Decimal("1400.00") * -1
    assert rows[1]["amount"] == Decimal("2800.00")
    assert any(row["amount"] < 0 for row in rows)
    assert any(row["amount"] > 0 for row in rows)


def test_semicolon_delimiter_sniffing():
    df = run_importer_sql(METRO_SQL, SEMICOLON_CSV)
    assert df.height == 2
    assert df["amount"].to_list() == [Decimal("2800.00"), Decimal("-87.43")]


def test_preamble_rows_sniffing():
    df = run_importer_sql(EXAMPLE_SQL, PREAMBLE_CSV)
    assert df.height == 2
    assert df["description"].to_list() == ["Coffee", "Tea"]


# ---------------------------------------------------------------------------
# all_varchar + casts
# ---------------------------------------------------------------------------


def test_all_varchar_raw_schema():
    con = _open_con()
    try:
        columns = load_raw(con, EXPORT_CSV)
    finally:
        con.close()

    assert columns == [
        RawColumn(name="date", type="VARCHAR"),
        RawColumn(name="amount", type="VARCHAR"),
        RawColumn(name="description", type="VARCHAR"),
    ]


def test_cast_behaviour_to_date_decimal_string():
    con = _open_con()
    try:
        load_raw(con, EXPORT_CSV)
        df = con.execute(EXAMPLE_SQL).pl()
    finally:
        con.close()

    assert df.schema["date"] == pl.Date
    assert df.schema["amount"] == pl.Decimal(38, 2)
    assert df.schema["description"] == pl.String


# ---------------------------------------------------------------------------
# Single-statement enforcement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE x",
        "CREATE TABLE t(a int)",
        "ATTACH ':memory:' AS other",
        "COPY (SELECT 1) TO '/tmp/out.csv'",
    ],
)
def test_assert_single_select_rejects(sql):
    with pytest.raises(ImporterSqlError) as excinfo:
        assert_single_select(sql)
    assert excinfo.value.stage == "parse"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE x",
        "CREATE TABLE t(a int)",
    ],
)
def test_run_importer_sql_rejects_non_select(sql):
    with pytest.raises(ImporterSqlError) as excinfo:
        run_importer_sql(sql, EXPORT_CSV)
    assert excinfo.value.stage == "parse"


def test_with_cte_select_is_allowed():
    df = run_importer_sql(
        "WITH filtered AS (SELECT * FROM raw WHERE "
        "TRY_CAST(amount AS DECIMAL(38,2)) < 0) "
        "SELECT CAST(date AS DATE) AS date, "
        "CAST(amount AS DECIMAL(38,2)) AS amount, "
        "CAST(description AS VARCHAR) AS description FROM filtered",
        EXPORT_CSV,
    )
    assert df.height == 9
    assert all(amount < 0 for amount in df["amount"].to_list())


# ---------------------------------------------------------------------------
# Accidents
# ---------------------------------------------------------------------------


def test_disk_read_is_blocked():
    with pytest.raises(ImporterSqlError) as excinfo:
        run_importer_sql("SELECT * FROM read_csv('/etc/passwd')", EXPORT_CSV)
    assert excinfo.value.stage == "query"
    assert "LocalFileSystem" in excinfo.value.message


def test_row_cap_is_enforced(monkeypatch):
    monkeypatch.setattr(settings, "importer_max_rows", 5)
    with pytest.raises(ImporterSqlError) as excinfo:
        run_importer_sql(EXAMPLE_SQL, EXPORT_CSV)
    assert excinfo.value.stage == "query"
    assert "row limit" in excinfo.value.message


def test_wall_clock_timeout_interrupts(monkeypatch):
    monkeypatch.setattr(settings, "duckdb_query_timeout_seconds", 0.3)
    with pytest.raises(ImporterSqlError) as excinfo:
        run_importer_sql(
            "SELECT count(*) AS date, 1 AS amount, 'x' AS description "
            "FROM range(10000000000)",
            b"a,b,c\n1,2,3\n",
        )
    assert excinfo.value.stage == "query"
    assert "Interrupt" in excinfo.value.message


# ---------------------------------------------------------------------------
# Contract validation
# ---------------------------------------------------------------------------


def test_missing_required_column():
    with pytest.raises(ImporterSqlError) as excinfo:
        run_importer_sql(
            "SELECT CAST(date AS DATE) AS date, "
            "CAST(amount AS DECIMAL(38,2)) AS amount FROM raw",
            EXPORT_CSV,
        )
    assert excinfo.value.stage == "validate"
    assert "description" in excinfo.value.message


def test_duplicate_output_names_rejected():
    with pytest.raises(ImporterSqlError) as excinfo:
        run_importer_sql(
            "SELECT CAST(date AS DATE) AS date, "
            "CAST(amount AS DECIMAL(38,2)) AS amount, "
            "CAST(description AS VARCHAR) AS description, "
            "CAST(description AS VARCHAR) AS description FROM raw",
            EXPORT_CSV,
        )
    assert excinfo.value.stage == "validate"
    assert "Duplicate" in excinfo.value.message
    assert "description" in excinfo.value.message


def test_extra_columns_are_dropped():
    df = run_importer_sql(
        "SELECT CAST(date AS DATE) AS date, "
        "CAST(amount AS DECIMAL(38,2)) AS amount, "
        "CAST(description AS VARCHAR) AS description, "
        "42 AS extra FROM raw",
        EXPORT_CSV,
    )
    assert df.columns == ["date", "amount", "description"]


def test_column_order_is_irrelevant():
    df = run_importer_sql(
        "SELECT CAST(description AS VARCHAR) AS description, "
        "CAST(amount AS DECIMAL(38,2)) AS amount, "
        "CAST(date AS DATE) AS date FROM raw",
        EXPORT_CSV,
    )
    assert df.columns == ["date", "amount", "description"]


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


def test_preview_success_shape():
    result = preview_importer(EXAMPLE_SQL, EXPORT_CSV)
    assert result.error is None
    assert result.total_rows == 11
    assert len(result.rows) == 11
    assert result.truncated is False
    assert result.rows[0] == {
        "date": "2025-12-18",
        "amount_cents": -1299,
        "description": "SPOTIFY PREMIUM",
    }
    assert result.raw_columns[0] == RawColumn(name="date", type="VARCHAR")
    assert len(result.raw_rows) == 11


def test_preview_truncates_display_only(monkeypatch):
    monkeypatch.setattr(settings, "importer_preview_display_rows", 3)
    monkeypatch.setattr(settings, "importer_raw_preview_rows", 2)

    result = preview_importer(EXAMPLE_SQL, EXPORT_CSV)

    assert result.error is None
    assert result.total_rows == 11
    assert len(result.rows) == 3
    assert result.truncated is True
    assert len(result.raw_rows) == 2


def test_preview_never_raises_parse_error():
    result = preview_importer("DROP TABLE raw", EXPORT_CSV)
    assert result.error is not None
    assert result.error.stage == "parse"
    # Raw schema is still reported even when the SQL is rejected.
    assert [column.name for column in result.raw_columns] == [
        "date",
        "amount",
        "description",
    ]


def test_preview_reports_query_error_on_disk_read():
    result = preview_importer(
        "SELECT * FROM read_csv('/etc/passwd')", EXPORT_CSV
    )
    assert result.error is not None
    assert result.error.stage == "query"


def test_preview_validates_beyond_display_window(monkeypatch):
    monkeypatch.setattr(settings, "importer_preview_display_rows", 3)

    lines = ["date,amount,description"]
    for i in range(8):
        # Row 6 (past the display window) has a blank description -> NULL.
        description = "" if i == 6 else f"row{i}"
        lines.append(f"2026-01-0{i + 1},1.00,{description}")
    blob = ("\n".join(lines) + "\n").encode()

    result = preview_importer(EXAMPLE_SQL, blob)

    assert result.error is not None
    assert result.error.stage == "validate"
    assert result.total_rows == 0
    assert result.rows == []


# ---------------------------------------------------------------------------
# Detection sweep
# ---------------------------------------------------------------------------


def test_run_importers_sql_parses_once_for_n_importers(monkeypatch):
    parse_calls = 0
    connect_calls = 0
    original_load_raw = duckdb_transform.load_raw
    original_connect = duckdb_transform._connect

    def counting_load_raw(con, blob):
        nonlocal parse_calls
        parse_calls += 1
        return original_load_raw(con, blob)

    def counting_connect():
        nonlocal connect_calls
        connect_calls += 1
        return original_connect()

    monkeypatch.setattr(duckdb_transform, "load_raw", counting_load_raw)
    monkeypatch.setattr(duckdb_transform, "_connect", counting_connect)

    importers = {1: EXAMPLE_SQL, 2: EXAMPLE_SQL, 3: METRO_SQL}
    results = run_importers_sql(importers, EXPORT_CSV)

    assert parse_calls == 1
    assert connect_calls == 1
    assert set(results) == {1, 2, 3}
    assert isinstance(results[1], pl.DataFrame)
    assert results[1].height == 11
    # Metro's SQL does not match the simple export -> a query error from the
    # missing "Credit" column.
    assert isinstance(results[3], ImporterSqlError)
    assert results[3].stage == "query"


def test_run_importers_sql_isolates_failures():
    importers = {
        1: EXAMPLE_SQL,
        2: "SELECT 1; DROP TABLE x",
        3: "SELECT * FROM read_csv('/etc/passwd')",
    }
    results = run_importers_sql(importers, EXPORT_CSV)

    assert isinstance(results[1], pl.DataFrame)
    assert isinstance(results[2], ImporterSqlError)
    assert results[2].stage == "parse"
    assert isinstance(results[3], ImporterSqlError)
    assert results[3].stage == "query"


def test_run_importers_sql_bad_csv_fails_all():
    # A PNG blob cannot be sniffed as CSV.
    png = bytes.fromhex("89504e470d0a1a0a0000000d49484452")
    results = run_importers_sql({1: EXAMPLE_SQL, 2: METRO_SQL}, png)
    errors = [
        value for value in results.values() if isinstance(value, ImporterSqlError)
    ]
    assert len(errors) == 2
    assert all(value.stage == "parse" for value in errors)
