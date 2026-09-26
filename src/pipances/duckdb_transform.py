"""DuckDB engine for user-authored SQL importers.

A user writes exactly one ``SELECT`` over a server-owned ``raw`` relation. The
``raw`` relation is loaded from the uploaded CSV bytes with every column typed
as ``VARCHAR`` (``all_varchar = true``), so the user is fully explicit about
casts. The result must satisfy the ``ImportedTransaction`` contract:
``date`` (Date), ``amount`` (Decimal(38,2)), ``description`` (String).

Everything runs in memory and the connection is locked down for accidents (not
malice): no local filesystem, no extension fetching, config locked, one
statement, resource caps, and a wall-clock timeout that interrupts the query.
"""

from __future__ import annotations

import io
import threading
from collections import Counter
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal

import duckdb
import polars as pl

from pipances.schemas import ImportedTransaction
from pipances.settings import settings

ErrorStage = Literal["parse", "query", "validate"]

REQUIRED_COLUMNS: tuple[str, ...] = ("date", "amount", "description")


class ImporterSqlError(Exception):
    """User-facing failure. ``stage`` maps to the UI error location."""

    stage: ErrorStage
    message: str

    def __init__(self, stage: ErrorStage, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class RawColumn:
    name: str
    type: str


@dataclass
class PreviewResult:
    raw_columns: list[RawColumn]
    raw_rows: list[list[str | None]]
    rows: list[dict[str, Any]]
    total_rows: int
    truncated: bool
    error: ImporterSqlError | None


def assert_single_select(sql: str) -> None:
    """Raise ``ImporterSqlError('parse')`` unless exactly one SELECT statement."""
    try:
        statements = duckdb.extract_statements(sql)
    except duckdb.Error as exc:
        raise ImporterSqlError("parse", f"Could not parse SQL: {exc}") from exc

    if len(statements) != 1:
        raise ImporterSqlError(
            "parse", "Importer SQL must be a single SELECT statement"
        )
    if statements[0].type != duckdb.StatementType.SELECT:
        raise ImporterSqlError(
            "parse", "Importer SQL must be a single SELECT statement"
        )


def _connect() -> duckdb.DuckDBPyConnection:
    """Open a locked-down, in-memory DuckDB connection."""
    con = duckdb.connect(
        config={
            "autoload_known_extensions": "false",
            "autoinstall_known_extensions": "false",
            "allow_community_extensions": "false",
            "threads": str(settings.duckdb_threads),
            "memory_limit": settings.duckdb_memory_limit,
        }
    )
    # Order matters: LocalFileSystem is a runtime setting, then lock everything.
    con.execute("SET disabled_filesystems = 'LocalFileSystem'")
    con.execute("SET lock_configuration = true")
    return con


@contextmanager
def _query_timeout(con: duckdb.DuckDBPyConnection) -> Iterator[None]:
    """Interrupt the connection if a query exceeds the wall-clock budget.

    Sync by design so it is usable from ``asyncio.to_thread`` in later
    workstreams: the enclosing call runs in a worker thread while the timer
    thread calls ``con.interrupt()``.
    """
    timer = threading.Timer(settings.duckdb_query_timeout_seconds, con.interrupt)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


def load_raw(con: duckdb.DuckDBPyConnection, blob: bytes) -> list[RawColumn]:
    """Register ``raw`` from in-memory bytes; return the sniffed schema.

    Raises ``ImporterSqlError('parse')`` if the CSV cannot be parsed.
    """
    try:
        relation = con.read_csv(io.BytesIO(blob), all_varchar=True)
        con.register("raw", relation)
        described = con.execute("DESCRIBE raw").fetchall()
    except (duckdb.Error, OSError) as exc:
        raise ImporterSqlError("parse", f"Could not parse the CSV file: {exc}") from exc

    return [RawColumn(name=row[0], type=row[1]) for row in described]


def _execute_and_validate(con: duckdb.DuckDBPyConnection, sql: str) -> pl.DataFrame:
    """Run one statement, enforce the contract, return the validated frame."""
    assert_single_select(sql)

    try:
        cursor = con.execute(sql)
    except duckdb.Error as exc:
        raise ImporterSqlError("query", f"Query failed: {exc}") from exc

    output_names = [column[0] for column in cursor.description]
    duplicates = sorted(
        name for name, count in Counter(output_names).items() if count > 1
    )
    if duplicates:
        raise ImporterSqlError(
            "validate",
            "Duplicate output column name(s): " + ", ".join(duplicates),
        )

    try:
        df = cursor.pl()
    except duckdb.Error as exc:
        raise ImporterSqlError("query", f"Query failed: {exc}") from exc

    missing = [name for name in REQUIRED_COLUMNS if name not in df.columns]
    if missing:
        raise ImporterSqlError(
            "validate",
            "Missing required column(s): " + ", ".join(missing),
        )

    if df.height > settings.importer_max_rows:
        raise ImporterSqlError(
            "query",
            f"Importer produced {df.height} rows, over the "
            f"{settings.importer_max_rows} row limit",
        )

    df = df.select(REQUIRED_COLUMNS)
    try:
        return ImportedTransaction.validate(df)
    except Exception as exc:  # patito raises a DataFrameValidationError
        raise ImporterSqlError("validate", str(exc)) from exc


def run_importer_sql(sql: str, blob: bytes) -> pl.DataFrame:
    """One-shot builder/detection call.

    Opens a connection, registers ``raw``, enforces one SELECT, executes, and
    validates the full contract result. Raises ``ImporterSqlError``.
    """
    con = _connect()
    try:
        with _query_timeout(con):
            load_raw(con, blob)
            return _execute_and_validate(con, sql)
    finally:
        con.close()


def run_importers_sql(
    importers: Mapping[int, str], blob: bytes
) -> dict[int, pl.DataFrame | ImporterSqlError]:
    """Detection sweep: ONE connection, ONE raw parse, N queries.

    Never raises; each value is the validated frame or the error.
    """
    results: dict[int, pl.DataFrame | ImporterSqlError] = {}

    con = _connect()
    try:
        with _query_timeout(con):
            try:
                load_raw(con, blob)
            except ImporterSqlError as exc:
                return {importer_id: exc for importer_id in importers}

            for importer_id, sql in importers.items():
                try:
                    results[importer_id] = _execute_and_validate(con, sql)
                except ImporterSqlError as exc:
                    results[importer_id] = exc
    finally:
        con.close()

    return results


def _display_rows(df: pl.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in df.to_dicts():
        value = row["date"]
        date_text = value.isoformat() if hasattr(value, "isoformat") else str(value)
        rows.append(
            {
                "date": date_text,
                "amount_cents": int(round(row["amount"] * 100)),
                "description": row["description"],
            }
        )
    return rows


def preview_importer(sql: str, blob: bytes) -> PreviewResult:
    """Builder Run. Never raises.

    Uses the same connection/validation path as ``run_importer_sql``, then
    slices the display rows. ``total_rows`` is the full validated count.
    """
    con = _connect()
    try:
        with _query_timeout(con):
            try:
                raw_columns = load_raw(con, blob)
            except ImporterSqlError as exc:
                return PreviewResult([], [], [], 0, False, exc)

            try:
                raw_result = con.execute(
                    "SELECT * FROM raw LIMIT ?",
                    [int(settings.importer_raw_preview_rows)],
                ).fetchall()
                raw_rows = [list(row) for row in raw_result]
            except duckdb.Error as exc:
                return PreviewResult(
                    raw_columns, [], [], 0, False, ImporterSqlError("query", str(exc))
                )

            try:
                df = _execute_and_validate(con, sql)
            except ImporterSqlError as exc:
                return PreviewResult(raw_columns, raw_rows, [], 0, False, exc)

            total_rows = df.height
            display = df.head(settings.importer_preview_display_rows)
            rows = _display_rows(display)
            return PreviewResult(
                raw_columns=raw_columns,
                raw_rows=raw_rows,
                rows=rows,
                total_rows=total_rows,
                truncated=total_rows > len(rows),
                error=None,
            )
    finally:
        con.close()
