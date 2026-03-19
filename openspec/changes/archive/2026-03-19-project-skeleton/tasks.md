## 1. Python Package Structure

- [x] 1.1 Run `uv init` to scaffold pyproject.toml and src layout
- [x] 1.2 Run `uv add` to add all dependencies: fastapi, uvicorn[standard], jinja2, python-multipart, polars, altair, aiosqlite, sqlalchemy[asyncio], itsdangerous
- [x] 1.3 Ensure `src/financial_pipeline/__init__.py` exists (create if uv init doesn't)

## 2. Nix Flake

- [x] 2.1 Create `flake.nix` with a default dev shell providing uv and tailwindcss standalone CLI (no Python from Nix — uv manages Python)

## 3. Verification

- [x] 3.1 Verify `uv sync` completes without errors
- [x] 3.2 Verify `uv run python -c "import financial_pipeline"` succeeds
