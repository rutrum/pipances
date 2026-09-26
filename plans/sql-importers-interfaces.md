# SQL Importers — Interface Freeze (Step 0)

Companion to `plans/sql-importers.md`. Every workstream codes against the exact
shapes below. Changing anything here after parallel work starts means re-syncing
multiple agents, so treat it as frozen once reviewed.

Branch: `duckdb-importer`. Verified dependency versions: `duckdb==1.5.5`,
`fsspec==2026.9.0`.

## 1. Engine — `src/pipances/duckdb_transform.py` (new)

```python
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import polars as pl

ErrorStage = Literal["parse", "query", "validate"]


class ImporterSqlError(Exception):
    """User-facing failure. `stage` maps to the UI error location."""
    stage: ErrorStage
    message: str


@dataclass(frozen=True)
class RawColumn:
    name: str
    type: str


@dataclass
class PreviewResult:
    raw_columns: list[RawColumn]
    raw_rows: list[list[str | None]]   # up to settings.importer_raw_preview_rows
    rows: list[dict[str, Any]]         # display slice, contract-shaped
    total_rows: int                    # full validated count
    truncated: bool                    # total_rows > len(rows)
    error: ImporterSqlError | None     # never raises


# Core helpers (module-private is fine, but these three are part of the contract)
def assert_single_select(sql: str) -> None:
    """Raise ImporterSqlError('parse') unless exactly one SELECT statement."""

def load_raw(con: duckdb.DuckDBPyConnection, blob: bytes) -> list[RawColumn]:
    """Register `raw` from in-memory bytes; return the sniffed schema.
    Raises ImporterSqlError('parse') if the CSV cannot be parsed."""


# Public entry points
def run_importer_sql(sql: str, blob: bytes) -> pl.DataFrame:
    """One-shot builder/detection call. Opens a connection, registers `raw`,
    enforces one SELECT, executes, validates the full contract result.
    Raises ImporterSqlError('parse' | 'query' | 'validate')."""

def run_importers_sql(
    importers: Mapping[int, str], blob: bytes
) -> dict[int, pl.DataFrame | ImporterSqlError]:
    """Detection sweep: ONE connection, ONE raw parse, N queries.
    Never raises; each value is the validated frame or the error."""

def preview_importer(sql: str, blob: bytes) -> PreviewResult:
    """Builder Run. Never raises. Uses the same connection/validation path as
    run_importer_sql, then slices the display rows."""
```

### Data-shape rules (frozen)

- `raw` is every column `VARCHAR`, loaded with `read_csv(BytesIO(blob), all_varchar=True)`.
- Connection config order: `duckdb.connect(config={...})` → `SET disabled_filesystems = 'LocalFileSystem'` → `SET lock_configuration = true`.
- Contract columns: `date` (Date), `amount` (patito `Decimal(38,2)`), `description` (String). Column order is irrelevant; selection is by name.
- Extra output columns are **dropped before** `ImportedTransaction.validate` (patito rejects superfluous columns). Missing required columns or **duplicate output names** raise `ImporterSqlError('validate')` with a message naming the offender. Duplicate names are read from DuckDB's raw `cursor.description`, before `.pl()` renames `x`/`x_1`.
- Exceeding `settings.importer_max_rows` raises `ImporterSqlError('query')` on the materialized result.
- `rows` display dicts use the existing preview shape: `{"date": "YYYY-MM-DD", "amount_cents": int, "description": str}`.
- Detection (`run_importers_sql`) does not compute raw/display previews.

## 2. Models — `src/pipances/models.py`

```python
class Importer(Base):
    __tablename__ = "importers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    sql: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

New nullable columns on `Import` (Phase 1 data only; not exposed in any UI/API yet):

```python
importer_id: Mapped[int | None] = mapped_column(
    ForeignKey("importers.id", ondelete="SET NULL"), nullable=True
)
importer_name: Mapped[str | None] = mapped_column(String)
importer_sql: Mapped[str | None] = mapped_column(Text)
```

`importers` is created by `create_all`. The three `Import` columns are added in
`migrations.py` with `PRAGMA table_info` guards + `ALTER TABLE`.

## 3. DB access — `src/pipances/db/importers.py` (new)

Session-first, async, mirroring `db/imports.py` conventions.

```python
async def list_importers(session: AsyncSession) -> Sequence[Importer]
async def get_importer(session: AsyncSession, importer_id: int) -> Importer | None
async def create_importer(session: AsyncSession, *, name: str, sql: str) -> Importer
async def update_importer(
    session: AsyncSession, importer_id: int, *, name: str | None, sql: str | None
) -> Importer | None
async def delete_importer(session: AsyncSession, importer_id: int) -> bool
```

Duplicate `name` surfaces as `sqlalchemy.exc.IntegrityError`; routes translate to
HTTP 409. Name is trimmed; empty name is a 422.

## 4. API — `routes/api/importers.py` + `routes/api/schemas.py`

| Method | Path | Request | Success | Errors |
|---|---|---|---|---|
| `GET` | `/api/importers` | — | `200 list[ImporterItem]` | — |
| `POST` | `/api/importers` | `ImporterCreate` | `201 ImporterItem` | 409 name, 422 invalid |
| `PATCH` | `/api/importers/{id}` | `ImporterUpdate` | `200 ImporterItem` | 404, 409, 422 |
| `DELETE` | `/api/importers/{id}` | — | `204` | 404 |
| `POST` | `/api/importers/preview` | multipart `file`, form `sql` | `200 ImporterPreviewResponse` | 413 too large |

Preview always returns 200 with the error embedded (no 4xx for bad SQL).

```python
class ImporterItem(BaseModel):
    id: int
    name: str
    sql: str
    created_at: str   # ISO
    updated_at: str   # ISO

class ImporterCreate(BaseModel):
    name: str
    sql: str

class ImporterUpdate(BaseModel):
    name: str | None = None
    sql: str | None = None

class RawColumnItem(BaseModel):
    name: str
    type: str

class ImporterPreviewError(BaseModel):
    stage: Literal["parse", "query", "validate"]
    message: str

class ImporterPreviewResponse(BaseModel):
    raw_columns: list[RawColumnItem]
    raw_rows: list[list[str | None]]
    rows: list[dict[str, Any]]
    total_rows: int
    truncated: bool
    error: ImporterPreviewError | None
```

The old `ImporterItem` (`name`, `filename`) is replaced. Nothing else in the
codebase consumes `filename`.

## 5. Settings — `src/pipances/settings.py`

Add (with these names and types); `importers_dir` is removed in Phase 2 by
workstream G, not here:

```python
duckdb_threads: int = 2
duckdb_memory_limit: str = "512MB"
duckdb_query_timeout_seconds: float = 10.0
importer_sql_max_length: int = 100_000
importer_upload_max_bytes: int = 20 * 1024 * 1024
importer_max_rows: int = 200_000
importer_preview_display_rows: int = 100
importer_raw_preview_rows: int = 20
```

## 6. Detection objects (Phase 2) — `src/pipances/ingest.py`

```python
@dataclass
class ImporterInfo:
    id: int
    name: str
    sql: str

async def discover_importers(database: Database) -> dict[int, ImporterInfo]

async def try_all_importers(database: Database, blob: bytes) -> dict[int, dict]:
    # value: {"success": True, "name": str, "df": pl.DataFrame}
    #      | {"success": False, "name": str, "error": str}

async def ingest(
    database: Database,
    df: pl.DataFrame,              # validated ImportedTransaction
    internal_account: str,
    importer_name: str,
    filename: str | None = None,
    *,
    importer_id: int | None = None,
    importer_sql: str | None = None,
) -> IngestResult
```

Rules:

- `discover_importers` reads the `importers` table via `db.importers.list_importers`.
  The importlib discovery code and `ImporterInfo.parse` are deleted.
- `try_all_importers` calls `run_importers_sql({id: sql}, blob)` once and maps
  each result to the dict shape above. Keys are importer ids.
- `ingest` sets `Import.importer_id`, `Import.importer_name`, and
  `Import.importer_sql` from its arguments. `Import.institution` keeps its
  current meaning (the importer display name, or `"Manual"`). Manual entry and
  any non-importer caller pass `importer_id=None` and `importer_sql=None`.
- Routes key on importer `id` (the `importer` form field is the id string). The
  selected importer's SQL runs through `run_importer_sql(info.sql, blob)` for
  dedup/commit, so builder preview and import share one execution path.
- `preview_dedup` keeps taking a validated `pl.DataFrame[ImportedTransaction]`.
- The existing `/import` temp-file mechanics are unchanged; detection now takes
  the uploaded bytes directly.

## 7. Browser contract — `static/js/pages/importers.js` (new)

- `window.__IMPORTERS__`: `Array<ImporterItem>` embedded by the page route.
- DOM ids: `#importers-table`, `#importer-modal`, `#importer-modal-title`,
  `#importer-name`, `#importer-sql`, `#importer-file`, `#importer-run`,
  `#importer-save`, `#importer-close`, `#importer-error`, `#importer-preview`,
  `#importer-raw-schema`, `#importer-summary`.
- Requests: `fetch("/api/importers", {method, headers: {"Content-Type": "application/json"}, body})`
  for CRUD; `FormData` with `file` + `sql` for preview.
- On save/create/delete, update the local `__IMPORTERS__` array and rebuild the
  Tabulator table in client mode; no page reload, no HTMX.
- Edit opens the modal populated from `__IMPORTERS__`; sample must be re-picked
  before Run.

## 8. Ownership map (no two workstreams share a file)

| WS | Owns |
|---|---|
| B | `src/pipances/duckdb_transform.py`, `tests/test_duckdb_transform.py`, new `duckdb_*` / `importer_*` keys in `src/pipances/settings.py` |
| C | `src/pipances/models.py`, `src/pipances/db/__init__.py`, `src/pipances/db/importers.py`, `src/pipances/db/migrations.py`, `tests/test_db.py` |
| D | `src/pipances/routes/api/importers.py`, `src/pipances/routes/api/schemas.py`, `tests/test_routes.py`, `tests/test_data_tables.py` |
| E | `src/pipances/routes/data.py`, `src/pipances/templates/**`, `static/js/pages/importers.js`, delete `static/js/pages/importers-table.js` |
| F | `src/pipances/ingest.py`, `src/pipances/routes/import_page.py`, `tests/test_import.py`, `tests/test_ingest.py`, `tests/conftest.py` (fixtures only), and only the `/import/*` tests in `tests/test_routes.py` |
| G | Phase 2 only: `src/pipances/settings.py` (remove `importers_dir`), `nix/**`, `README.md`, `CHANGELOG.md`, delete `importers/` |
| H | `tests/ui/**` |
