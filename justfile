default: serve

# Build Tailwind CSS (with DaisyUI)
css:
    tailwindcss -i input.css -o static/css/style.css

# Build minified CSS for production
css-min:
    tailwindcss -i input.css -o static/css/style.css --minify

# Watch templates and rebuild CSS on changes
css-watch:
    tailwindcss -i input.css -o static/css/style.css --watch

# Install Python dependencies
sync:
    uv sync

# Run the dev server
serve: css
    uv run python -m financial_pipeline.main

# Build CSS and sync deps (fresh checkout setup)
setup: sync css

# Lint Python (ruff) and templates (djlint)
lint:
    uv run ruff check src/ importers/
    uv run djlint src/financial_pipeline/templates/ --lint

# Format Python (ruff) and templates (djlint)
fmt:
    uv run ruff format src/ importers/
    uv run ruff check --fix src/ importers/
    uv run djlint src/financial_pipeline/templates/ --reformat

# Full check (CI-style, exits non-zero on issues)
check:
    uv run ruff format --check src/ importers/
    uv run ruff check src/ importers/
    uv run djlint src/financial_pipeline/templates/ --lint
