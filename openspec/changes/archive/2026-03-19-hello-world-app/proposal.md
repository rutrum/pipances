## Why

The project skeleton exists but there's no running application yet. We need a FastAPI app serving a styled page to validate the full stack: FastAPI + Jinja2 templates + HTMX + Tailwind CSS + DaisyUI. This merges CHANGES items 2 and 3 to go straight to compiled Tailwind rather than using CDN as an intermediate step.

## What Changes

- Create FastAPI app with uvicorn entrypoint in `src/financial_pipeline/main.py`
- Create Jinja2 base template loading HTMX (CDN) and compiled Tailwind CSS
- Set up Tailwind CSS build pipeline with DaisyUI plugin using the standalone CLI
- Configure static file serving for the compiled CSS output
- Single index route rendering a styled hello-world page

## Capabilities

(none — this is app infrastructure, not a user-facing capability)

## Impact

- New files: `main.py`, templates directory, Tailwind config, input CSS, static directory
- New dev workflow: Tailwind CSS must be built before/during development
- App becomes runnable via `uv run python -m financial_pipeline.main`
