# DuckDB SQL Importers — Plan

Branch: `duckdb-importer`.

Replace the filesystem Python importers with DB-backed DuckDB SQL importers.
Users build transformations interactively in the browser against a sample CSV,
preview the transformed rows live, and save the SQL. The saved SQL runs in a
DuckDB runtime on every real import, fully in memory.

## Goal

1. The only importer artifact is a SQL string stored in the database. No
   `importers/*.py`, no `PIPANCES_IMPORTERS_DIR`, no importlib discovery.
2. A browser builder lets the user upload a sample CSV, write a SQL `SELECT`
   over a `raw` relation, run it, and see the resulting rows and any validation
   error before saving. Files are held in memory, never written to disk.
3. Detection semantics are unchanged: on upload, every saved importer is tried
   against the file, all successes are offered, and a single success is
   auto-selected. Commit/dedup/ML paths are untouched.

## Status

Agents update this table when their workstream's gate passes.

| Workstream | State | Notes |
|---|---|---|
| A — build spike | done | `duckdb==1.5.5`, `fsspec==2026.9.0` build under uv2nix + Nix with no override. Also relocated `nix/lib/assets.nix` -> `nix/assets.nix` to fix a pre-existing blueprint evaluation failure; recommend isolating that as its own commit before merge. |
| Step 0 — interface freeze | done | `plans/sql-importers-interfaces.md` |
| B — engine | done | `duckdb_transform.py` + engine tests green; adds the new `duckdb_*` / `importer_*` settings keys (keeps `importers_dir` for G). Deviations resolved in the interface doc. |
| C — model + DB | done | `models.py` (`Importer` + 3 `Import` provenance columns), `db/migrations.py` (`migrate_imports`), `db/__init__.py`, new `db/importers.py`, db tests green. No interface-shape change; one clarification recorded below (CRUD flushes, caller commits). |
| D — API | blocked | on B + C |
| E — UI | blocked | on D |
| F — detection cutover | Phase 2 | on B + C + D |
| G — cleanup | Phase 2 | on F |
| H — Playwright | Phase 2 | on E |

## The seam

Only `importer.parse(blob) -> pl.DataFrame` changes. Everything downstream is
indifferent to how the DataFrame was produced:

```
blob ──▶ DuckDB `raw` (all VARCHAR) ──▶ user SQL ──▶ ImportedTransaction.validate ──▶ ingest()
                                                            │
                                                            ├─ preview_dedup
                                                            └─ _predict_for_transactions
```

The SQL contract is the old function contract renamed to columns: the query
must return `date` (DATE), `amount` (DECIMAL(38,2)), `description` (VARCHAR).
`ImportedTransaction` (patito/polars), `ingest`, `preview_dedup`, and manual
entry all stay as-is. Blast radius is `discover_importers`,
`try_all_importers`, the importer model/table, the importer API/UI, and the
settings/nix plumbing.

## Locked decisions

| # | Decision |
|---|---|
| 1 | DuckDB SQL is the only dialect. Python importers are deleted, no fallback. |
| 2 | `raw` is loaded with `all_varchar = true` so the user is fully explicit with casts. |
| 3 | The `read_csv(...)` load is server-owned; the user writes the `SELECT`/`WITH` that references `raw`. |
| 4 | The runtime is locked down for accidents, not malice: no local filesystem, no statement mutation, resource caps, timeout. |
| 5 | Editor is a plain `<textarea>` with a Run button. No CodeMirror/Monaco in v1. |
| 6 | Detection behavior is unchanged: try all, auto-pick the sole success. |
| 7 | No CSV options form in v1; DuckDB auto-detection of header/delimiter only. |
| 8 | Samples are never persisted; editing an importer re-uploads a sample. |
| 9 | Saving does not require a successful run: save-as-draft with a warning. |
| 10 | `ImportedTransaction` keeps the strict `DECIMAL(38,2)` amount type. |
| 11 | No seeded example importer. |
| 12 | The importer feature moves off HTMX. New interactions are JSON `/api` calls driven by first-party JS; no new `hx-*` attributes. |
| 13 | The `/data/importers` page ships the importer list and builder markup on load; no per-step HTML fragment endpoints. |
| 14 | The uploaded sample lives in memory only. Nothing under `importers/` and no temp CSV on disk. |
| 15 | `Import` records `importer_id`/`importer_name`/`importer_sql` for audit; not surfaced in UI yet. |
| 16 | User SQL must be exactly one `SELECT`, enforced with `duckdb.extract_statements`, not a string wrap. |
| 17 | A detection sweep uses one DuckDB connection and parses the CSV once for all importers. |
| 18 | Preview validates the whole file; only the rendered rows are truncated. |
| 19 | Preview errors are `{stage, message}`. |

## The contract and the "lie"

The editor shows a read-only preamble (rendered HTML, not part of the
submitted SQL):

```sql
-- raw is loaded for you from the uploaded file, every column as VARCHAR:
--   SELECT * FROM read_csv('input_file.csv', all_varchar = true)
```

The user then writes, e.g.:

```sql
SELECT
  CAST("Transaction Date" AS DATE)              AS date,
  (CAST("Credit" AS DECIMAL(38,2)) * -1)        AS amount,
  CAST("Memo" AS VARCHAR)                        AS description
FROM raw
WHERE "Credit" IS NULL OR "Credit" = ''
```

Server-side, `raw` is a DuckDB relation built from the in-memory bytes. The
user's query is never concatenated with the preamble; the preamble is
illustrative only. `raw` is in scope like a table, so the user's query may
start with `WITH`. Validation errors come from `ImportedTransaction.validate`
after the query runs, so missing columns and wrong types surface as a readable
message.

## Engine: verified in-memory CSV + DuckDB

Spiked against DuckDB 1.5.5. The approach below was tested and works; details
are in "Verified spike results".

```python
con = duckdb.connect(config={
    "autoload_known_extensions": "false",
    "autoinstall_known_extensions": "false",
    "allow_community_extensions": "false",
    "threads": str(settings.duckdb_threads),
    "memory_limit": settings.duckdb_memory_limit,
})
# Order matters: LocalFileSystem is a runtime setting, then lock everything.
con.execute("SET disabled_filesystems = 'LocalFileSystem'")
con.execute("SET lock_configuration = true")

# BytesIO is parsed by DuckDB's sniffer entirely in memory (requires fsspec).
con.register("raw", con.read_csv(io.BytesIO(blob), all_varchar=True))

# Exactly one SELECT, enforced before execution (see "Single statement").
assert_single_select(user_sql)
df = con.execute(user_sql).pl()
```

Properties, all confirmed by the spike:

- Semicolon-delimited files and files with preamble rows are sniffed correctly.
- Every column is `VARCHAR`, so the user is explicit.
- `read_csv('/etc/passwd')` is rejected by the disabled local filesystem.
- `duckdb.extract_statements()` reports statement count and type, so we require
  exactly one `SELECT` before execution. `SELECT 1; DROP TABLE x` reports two
  statements and is rejected; `WITH ... SELECT` reports one `SELECT` and is
  allowed. Verified against DuckDB 1.5.5.
- The result converts to a polars DataFrame; `CAST(... AS DECIMAL(38,2))`
  and `CAST(... AS DATE)` land as patito-compatible dtypes.

Two hard constraints discovered:

- `read_csv` from a `BytesIO` requires the `fsspec` Python package. It uses
  fsspec's in-memory filesystem, so this is still no-disk.
- `enable_external_access = false` also blocks the in-memory filesystem, so it
  cannot be combined with in-memory `read_csv`. We get the accident protection
  from `disabled_filesystems = 'LocalFileSystem'` (blocks real files),
  `lock_configuration`, no extension autoload/install, and the single-statement
  check instead.

### Single statement

The engine validates the user's SQL before executing it:

```python
def assert_single_select(sql: str) -> None:
    stmts = duckdb.extract_statements(sql)
    if len(stmts) != 1 or stmts[0].type != duckdb.StatementType.SELECT:
        raise ImporterSqlError(stage="parse", message="Importer SQL must be a single SELECT")
```

This is preferred over wrapping the query in a subquery: error positions still
point at the user's real line/column, DuckDB's `FROM raw SELECT ...` syntax keeps
working, and non-`SELECT` statements are rejected by type rather than by a
parser error. There is no `LIMIT` applied to validation (see preview below);
when a display slice is needed it is taken from the materialized result.

### One connection per sweep

`run_importer_sql(sql, blob)` is the builder's single-shot entry point. Detection
uses `run_importers_sql(importers, blob)`, which opens one connection, registers
`raw` once, and runs each importer's SQL as a relation on that connection. This
parses and sniffs the CSV once for all N importers instead of N times.

### Verified spike results

```
semicolon sniff:       OK -> ['Transaction Date', 'Debit', 'Credit', 'Memo']
semicolon values:      OK -> [('02/15/2026', None, '2800.00', 'EMPLOYER DIRECT DEP')]
preamble sniff:        OK -> ['Date', 'Amount', 'Description']
preamble values:       OK -> [('2026-01-15', '19.99', 'Coffee')]
disk read blocked:     BLOCKED -> PermissionException (LocalFileSystem disabled)
extract_statements:    "SELECT 1; DROP TABLE x" -> 2 stmts; "WITH ... SELECT" -> 1 SELECT
polars register+cast:  OK -> Decimal(38,2), Date, String
```

Spike to run as the first implementation task: confirm DuckDB's wheel builds
under uv2nix (may need `autoPatchelfHook`, or a nixpkgs duckdb). That is the
only unknown left.

## Sandbox posture

The bar is **accident prevention, not malice**; the user owns the system.

| Layer | Mechanism | Stops |
|---|---|---|
| No real filesystem | `SET disabled_filesystems = 'LocalFileSystem'` | stray `read_csv('/etc/passwd')`, `ATTACH` to files |
| Config lock | `SET lock_configuration = true` | user SQL re-enabling anything |
| No extension fetching | autoload/autoinstall/community off | network via `httpfs` and friends |
| Single statement | `extract_statements` requires one `SELECT` | multi-statement, `COPY`, `ATTACH`, DDL/DML |
| Resource caps | `memory_limit`, `threads`, upload/SQL length caps | memory/CPU blowups |
| Wall-clock timeout | `asyncio.to_thread` + `threading.Timer` calling `con.interrupt()` | runaway scans |

No OS-level isolation or subprocess sandboxing. The connection is created per
execution and closed after; nothing of the user's file touches disk.

## Data model

New `Importer` in `models.py`:

```python
class Importer(Base):
    __tablename__ = "importers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    sql: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = ...
    updated_at: Mapped[datetime] = ...
```

`Base.metadata.create_all` creates it; no `ALTER TABLE` migration needed. No
`enabled`/priority column in v1 (detection is still "try all"). Unique `name`
keeps the list and picker unambiguous; duplicate names return a friendly 409,
matching how account name conflicts are handled.

New `db/importers.py` with session-first queries: `list_importers`,
`get_importer`, `create_importer`, `update_importer`, `delete_importer`.

### Import provenance (data only, not surfaced yet)

Add to `Import`:

- `importer_id` — nullable FK to `importers` (`ON DELETE SET NULL`)
- `importer_name` — name snapshot at import time
- `importer_sql` — SQL snapshot actually executed

These are populated during the Phase 2 cutover and are **data-model only in this
work**: nothing in the UI or API exposes them yet. They make future audit and
re-run features possible, and keep history meaningful when an importer is edited
or deleted. Because they are new columns on an existing table, they go through
`migrations.py` (`PRAGMA table_info` guard + `ALTER TABLE`) rather than relying
on `create_all`.

## API and UI: client-side, no HTMX

The `/data/importers` page is an early step of the HTMX-to-JS shift. It does
not add any `hx-*` attributes. The server renders the page shell, embeds the
full importer list (including SQL) as JSON, ships the builder modal markup, and
loads a first-party script. Everything after that is `/api` plus JS.

### Page: `GET /data/importers`

- Renders the list, the builder modal, and `window.__IMPORTERS__ = [...]`
  (id, name, sql, updated_at) so the client needs no extra fetch to populate
  the table or open the edit form.
- Tabulator runs in client mode over the embedded array (no `ajaxURL`), with
  Edit/Delete action buttons and a "New Importer" button.
- `static/js/pages/importers.js` owns all state and API calls.

### API

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/api/importers` | — | list of `{id, name, sql, created_at, updated_at}` |
| `POST` | `/api/importers` | `{name, sql}` | created row (409 on duplicate name) |
| `PATCH` | `/api/importers/{id}` | `{name?, sql?}` | updated row |
| `DELETE` | `/api/importers/{id}` | — | `204` |
| `POST` | `/api/importers/preview` | multipart `file` + `sql` | preview payload |

`POST /api/importers/preview` is stateless and writes nothing to disk: it
receives the CSV bytes, runs the engine on them, and returns:

```json
{
  "raw_columns": [{"name": "Transaction Date", "type": "VARCHAR"}],
  "raw_rows": [["02/15/2026", null, "2800.00", "EMPLOYER DIRECT DEP"]],
  "rows": [{"date": "2026-02-15", "amount_cents": -280000, "description": "..."}],
  "total_rows": 4213,
  "truncated": true,
  "error": null
}
```

`raw_columns`/`raw_rows` let the user see what the sniffer inferred (and the
exact column names to quote). `rows` is the transformed, contract-shaped result
capped at `settings.importer_preview_display_rows` for rendering, while
`total_rows` reports the full validated count and `truncated` says whether the
display was cut.

Validation runs against the **whole file**, not the display window. The query
executes without a `LIMIT`, the full result is validated through
`ImportedTransaction.validate`, and only then is the display sliced. This is the
same work the real import does, so a preview that passes will import. A bank
export is at most a few MB and tens of thousands of rows, and `memory_limit`,
the wall-clock timeout, and `settings.importer_max_rows` bound the worst case
(over the cap returns a clear error instead of an OOM).

Errors are normalized into a machine-readable shape so the client can point at
the right input:

```json
{"error": {"stage": "parse" | "query" | "validate", "message": "..."}}
```

`parse` means the single-`SELECT` check failed, `query` means DuckDB failed to
execute, and `validate` means the output did not satisfy the
`date`/`amount`/`description` contract. Keeping the error in a 200 payload
avoids duplicating error handling on the client.

The sample is re-sent on each Run. Files are small bank exports, so this keeps
the endpoint stateless. If iteration cost becomes real, add an in-memory LRU
keyed by a client-generated sample id (still no disk); that is a follow-up, not
v1.

### Builder behaviour (`importers.js`)

- State: `editingId`, `sampleFile`.
- New: opens the modal blank. Edit: opens the modal populated from the embedded
  list; the sample must be re-selected before Run.
- Run: `POST /api/importers/preview` with the current SQL and sample; renders
  the raw schema/rows and the transformed preview (a plain DaisyUI
  `table table-zebra`, no Tabulator needed for ≤100 rows) or the error.
- Save: `PATCH` when `editingId` else `POST`; on success update the embedded
  array and rebuild the Tabulator table. A warning is shown if the last Run
  errored, but saving still succeeds (decision 9).
- Delete: `DELETE`, then rebuild the table.
- The preview table and editor use existing DaisyUI classes; no new styling
  system.

Reused only where it already fits: the temp-token helpers in
`routes/import_page.py` stay untouched for the existing `/import` flow, and are
not used by the builder.

## Import flow changes (Phase 2)

- `discover_importers(database) -> dict[int, ImporterInfo]` becomes async and
  DB-backed; `ImporterInfo` carries `id`, `name`, and `sql`.
- `try_all_importers(database, blob: bytes)` becomes async and takes bytes,
  calling `run_importers_sql(importers, blob)` to share one connection and one
  CSV parse, then ``ImportedTransaction.validate`` per importer.
- The import routes switch from `importer_key` (module name) to importer `id`.
  The existing temp-file mechanics of `/import/preview` are left alone except
  that detection no longer needs the file on disk.
- `ingest` and `preview_dedup` are unchanged.

## Cleanup

- Delete `importers/` (`example.py`, `metro_cu.py`) and the importlib discovery
  code.
- Remove `importers_dir` from `settings.py`, the `importers` derivation in
  `nix/packages/pipances.nix`, the `importersDir` option and tmpfiles/sandbox
  wiring in `nix/modules/nixos/pipances.nix`, and `PIPANCES_IMPORTERS_DIR` in
  `nix/packages/docker.nix`.
- Update `README.md` (Custom Importers section, settings table) and
  `CHANGELOG.md`.
- Add `duckdb` and `fsspec` to `pyproject.toml`; regenerate `uv.lock`.
- Update `tests/test_import.py` and `tests/test_ingest.py`.

## Phased implementation

Two phases. Phase 1 lands the engine, schema, API, and UI, leaving the existing
Python detection path live. Phase 2 flips detection/ingest to the SQL importers
and deletes the Python path.

### Phase 1 — engine, data structures, API, UI

1. **Engine + build spike.** Add `duckdb` + `fsspec`; confirm the wheel builds
   under uv2nix. New `src/pipances/duckdb_transform.py` with
   `run_importer_sql(sql, blob)` (builder) and `run_importers_sql(importers, blob)`
   (detection sweep, one connection), implementing the verified sequence and
   `assert_single_select`. Nothing touches disk.
2. **Model + DB access.** `Importer` model and `db/importers.py` queries, plus
   the `Import` provenance columns and their `migrations.py` entries.
   Migration-free table creation for `importers`, unique-name conflict handling.
3. **API.** Extend `routes/api/importers.py` with the CRUD routes, the
   preview route, and Pydantic schemas. Update `GET /api/importers`.
4. **UI.** Rework `/data/importers` to embed the list, render the builder
   modal, and load `static/js/pages/importers.js`. Remove the old
   `importers-table.js` ajax wiring. Python importers still power `/import`,
   so the feature is usable end to end before the cutover.
5. **Tests for Phase 1.** Engine unit tests, sandbox/accident tests, API
   route tests, browser verification.

### Phase 2 — logic replacement

6. **Import flow cutover.** Async DB-backed `discover_importers` /
   `try_all_importers`; importer-id keys in the import routes. A saved draft
   that never ran simply fails detection like a bad Python importer did.
7. **Delete the Python path.** `importers/`, `importers_dir`, the nix
   derivation and module option, and the docker env.
8. **Cleanup + tests.** Settings, README/CHANGELOG, updated import tests,
   browser verification of detection/commit.

## Test plan

- Engine: `run_importer_sql` on `example.csv` and the split debit/credit Metro
  CU shape (semicolon/preamble variants); `all_varchar` cast behaviour;
  single-statement rejection; full-file validation catches an error that only
  appears after the display window; validation errors for missing columns,
  wrong types, duplicate output names, and extra columns.
- Detection reuse: one connection sweep over N importers parses the CSV once
  (assert the sniffer/parse is not repeated per importer).
- Accidents: disk read is blocked; multi-statement/`COPY`/`ATTACH` are
  rejected by `assert_single_select`; timeout interrupts a long query; caps are
  applied.
- API: CRUD happy path and duplicate-name 409; preview returns raw schema,
  transformed rows, and a readable error; sample bytes are never written to
  disk (assert no file appears under the temp dir).
- UI/browser: build, run, save, edit, delete; then a real CSV on `/import`
  after the cutover.
- Existing: `ingest`, `preview_dedup`, and split/date tests stay green.

## Resolved in discussion

- CSV options: auto-detect only for v1 (7). Revisit with saved parse options
  if a real bank format needs `skip`/delimiter/encoding.
- Samples: never persisted (8); editing re-uploads.
- Save gate: save-as-draft with a warning (9).
- Amount: strict `DECIMAL(38,2)` (10); cast hints come later.
- No seeded example (11).
- No new HTMX; `/api` + first-party JS (12, 13).
- In-memory only, no temp CSV (14).
- Provenance columns on `Import` land as data now, UI later (15).
- Single-statement enforcement via `extract_statements`, no string wrap (16).
- One DuckDB connection (and one CSV parse) per detection sweep (17).
- Preview/validate the whole file; only the display is truncated (18).
- Preview errors normalized to `{stage, message}` (19).

### Workstream B deviations (resolved)

Recorded 2026-03 (B implementation), then folded into
`plans/sql-importers-interfaces.md`:

1. **`importers_dir` not removed.** Interface section 5 wording was ambiguous;
   now states that G removes it in Phase 2. B correctly added only the new keys.
2. **Extra output columns are dropped *before* `ImportedTransaction.validate`.**
   Section 1 now says so, because patito raises `Superfluous column` otherwise.
   Duplicate output names are detected from DuckDB's raw `cursor.description`
   (before `.pl()` renames `x`/`x_1`) and rejected as `validate`.
3. **`importer_max_rows` over-cap is a `query`-stage error.** Section 1 now
   assigns that stage.

### Workstream C deviations (resolved)

Recorded 2026-03 (C implementation). No interface-shape change; one
clarification for D:

1. **CRUD functions `flush()` but do not `commit()`.** Interface section 3 says
   "session-first", and the repo convention (`db/transactions.py`) leaves
   transaction boundaries to the caller. `create_importer` / `update_importer`
   flush so the unique-name constraint raises `IntegrityError` inside the call;
   `delete_importer` flushes too. **D's routes own `commit()` and the 409
   translation.** `create_importer`/`update_importer` strip the name; the
   non-empty (422) check stays route-side, matching `routes/api/accounts.py`.

## Agent execution plan

The work is shaped for parallel agents: after one interface-freeze step, the
workstreams touch disjoint files and gate on explicit commands.

### Step 0 — interface freeze (done)

Frozen in `plans/sql-importers-interfaces.md`: engine signatures, Pydantic
models, table shapes, JS contract, settings names, and the ownership map. Every
workstream codes against it and must not silently change it; a deviation gets
recorded here and in the plan before proceeding.

### Workstreams

| WS | Scope | Owned files | Depends on | Gate |
|---|---|---|---|---|
| A | Build spike: duckdb/fsspec wheel under uv2nix — **done** | `pyproject.toml`, `uv.lock`, flake files | — | `uv sync`, `nix build` |
| B | Engine + new settings keys | new `duckdb_transform.py`, `tests/test_duckdb_transform.py`, new keys in `settings.py` | A, Step 0 | engine tests |
| C | Model + DB + migrations | `models.py`, `db/importers.py`, `db/migrations.py`, db tests | Step 0 | db tests |
| D | API + schemas | `routes/api/importers.py`, `routes/api/schemas.py`, route tests | B, C | API tests |
| E | UI: page, modal, `importers.js` | `routes/data.py`, templates, `static/js/pages/importers.js` | D | lint + agent-browser |
| F | Phase 2 detection cutover | `ingest.py`, `routes/import_page.py`, `tests/test_import.py`, `tests/test_ingest.py` | B, C, D | `just test` |
| G | Phase 2 cleanup | `settings.py`, `nix/**`, `README.md`, `CHANGELOG.md`, delete `importers/` | F | `just lint`, `nix build` |
| H | Playwright coverage | `tests/ui/**` | E | `just test-ui` |

Parallelization: A first (it can invalidate the dependency choice). Once A and
Step 0 land, **B and C run in parallel**. D follows both. E and F can then run
in parallel. G is last. H follows E.

### Conflict avoidance

- One writer per file. C owns `models.py`, `db/__init__.py`, and
  `db/migrations.py`; D and E never touch them. B owns `duckdb_transform.py` and
  the new `settings.py` keys; F owns `ingest.py`; G owns nix/docs and, in
  Phase 2, removes `importers_dir` from `settings.py`; E owns templates and
  `importers.js`.
- Run each parallel agent in its own `git worktree` off `duckdb-importer` and
  merge in dependency order (A, C/B, D, E/F, G, H), then have one integration
  run execute the full suite. Two agents editing one working tree will corrupt
  each other even with disjoint files.
- Agents do not commit or push (repo rule); the orchestrator reviews and the
  user commits.

### Verification gates

- `just lint` after every workstream, mandatory.
- `just test` for B, C, D, F.
- `just test-ui` for E, H; agent-browser for E's interactive check.
- A workstream is not done until its gate passes on the merged branch, not just
  in its worktree.

### Per-agent brief

Each agent gets: the plan path, the Step 0 appendix, its WS row (scope, owned
files, dependencies, gate), and the standing rules to stay inside its file set,
not commit/push, and run `just lint` before reporting done. The dependency row
is the coordination contract; an agent should stop and report rather than reach
into another workstream's files.

## Future considerations

**duckdb-wasm client-side preview.** DuckDB ships a WASM build, so the builder's
Run could execute entirely in the browser, removing the preview round-trip. Not
v1: it means vendoring a multi-megabyte WASM bundle and worker setup through
`nix/lib/assets.nix`, loading the CSV in the browser, and keeping two execution
paths in sync. The server runtime is still needed for real imports, so WASM is
a preview-latency win, not a replacement. Worth a spike after ship.

**In-memory sample cache.** If re-sending the sample on every Run is too much,
cache bytes under a client-generated id in a bounded in-process dict. Still no
disk.

**Importer enable/disable or priority.** If the list grows and a bad importer
is noisy, add an `enabled` flag and filter in `discover_importers`.
