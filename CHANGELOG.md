# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-09-24

This release replaces the hand-rolled HTMX table stack with a JSON API and Tabulator tables, and reorganizes the database and configuration layers.

### Added

- JSON API under `/api` for accounts, categories, importers, imports, inbox, and transactions, plus Tabulator-native `*.table` endpoints that return Tabulator's remote `last_page`/`last_row`/`data` envelope.
- Tabulator-based inbox with inline editing, single-row and batch updates, an edit modal, transaction splits, and the stage/approve/commit flow.
- Tabulator-based Explore and `/data` tables for transactions, accounts, categories, external accounts, importers, and imports.
- Tabulator CSV import preview table.
- Range selection and clipboard paste for bulk inline edits.
- Tom Select combo boxes (remote search, custom rendering, multi-select) replacing the hand-rolled Alpine combo boxes.
- `pipances.db` package of session-first query helpers for accounts, categories, imports, and transactions; transaction boundaries are owned by the caller.
- Central `Settings` (pydantic-settings) for paths and application constants, configurable through `PIPANCES_*` environment variables.
- Dead-code checker (`just deadcode`) combining ast-grep rules with vulture, plus a custom `tabulator-daisy` stylesheet.
- Vendored Tabulator JS/CSS flake inputs and Tabulator/Tom Select skill docs.
- New unit and API tests, plus rewritten UI tests for the inbox, data tables, sorting, table editing, and splits.

### Changed

- Inbox, Explore, and Data pages read and write through the JSON API instead of server-rendered HTMX partials.
- Static asset cache busting uses per-file mtimes instead of a global version string.
- `httpx` replaced with `httpx2`; linting consolidated into `prek` (ruff, djlint, tombi, ast-grep, ty, typos, nixfmt).
- Flake inputs bumped (blueprint, nixpkgs, uv2nix); Jinja templates linted and reformatted with djlint.

### Removed

- Legacy HTMX table stack: table partials, custom combo boxes, pagination, and the endpoints that backed them.
- `openspec` and `beads`; unused helpers in `pipances.utils`.

### Fixed

- Tom Select dropdowns no longer render behind the edit modal, overflow narrow table cells, or conflict with Tabulator arrow-key navigation.
- Packaged deployments start without `PIPANCES_IMPORTERS_DIR` or `PIPANCES_TEMP_DIR` set, and templates resolve from the installed package rather than a source-checkout path.

## [0.1.0] - 2026-05-26

Initial release: a self-hosted, SQLite-backed finance tracker built around mandatory human review of automatically imported transactions.

### Added

- CSV import from bank exports through user-written Python importers.
- ML prediction of description, external account, and category, trained on previously approved transactions.
- Inbox review workflow with bulk staging and commit as the human sign-off step.
- Explore page with Altair/Vega-Lite charts, summary statistics, and filtered transaction browsing.
- Management pages for accounts, categories, external accounts, importers, and imports.
- Account lifecycle fields (kind, active, starting balance, balance date) and transaction splits.
- SQLite storage via SQLAlchemy async and aiosqlite, with schema migrations run at startup.
- Nix flake providing a package, NixOS module, OCI container image, and dev shell.
