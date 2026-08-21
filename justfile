default:
    just --list

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
    uv run python -m pipances.main

# Build CSS and sync deps (fresh checkout setup)
setup: sync css

# Lint and format (via prek — all files)
lint:
    prek run --all-files

# Reset the database and seed with test data; will trigger server hot-reload
seed:
    rm -f pipances.db
    uv run python scripts/seed.py
    touch src/pipances/__init__.py

# Run unit/API tests (no browser required)
test:
    uv run pytest tests/ -v --ignore=tests/ui

# Run UI/browser tests against a live server with seeded data
test-ui:
    uv run pytest tests/ui/ -v --base-url=http://localhost:8099 --asyncio-mode=strict

# Run all tests (unit + UI)
test-all:
    uv run pytest tests/ -v
