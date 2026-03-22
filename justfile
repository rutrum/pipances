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

# Run the dev server (kills any existing instance first)
serve: css _kill-server
    uv run python -m financial_pipeline.main

# Kill any running dev server on port 8097
_kill-server:
    #!/usr/bin/env bash
    pids=$(ss -tlnp 2>/dev/null | grep ':8097 ' | grep -oP 'pid=\K\d+' | sort -u)
    if [ -n "$pids" ]; then
        echo "Killing existing server(s) on port 8097: $pids"
        echo "$pids" | xargs kill 2>/dev/null
        sleep 1
    fi

# Build CSS and sync deps (fresh checkout setup)
setup: sync css

# Lint Python (ruff) and templates (djlint)
lint:
    uv run ruff check src/ importers/ tests/
    uv run djlint src/financial_pipeline/templates/ --lint

# Format Python (ruff) and templates (djlint)
fmt:
    uv run ruff format src/ importers/ tests/
    uv run ruff check --fix src/ importers/ tests/
    uv run djlint src/financial_pipeline/templates/ --reformat

# Delete the database file
reset-db:
    rm -f financial_pipeline.db

# Reset the database and seed with test data; will trigger server hot-reload
seed: reset-db
    uv run python scripts/seed.py
    touch src/financial_pipeline/__init__.py

# Run tests
test:
    uv run pytest tests/ -v

# Full check (CI-style, exits non-zero on issues)
check:
    uv run ruff format --check src/ importers/ tests/
    uv run ruff check src/ importers/ tests/
    uv run djlint src/financial_pipeline/templates/ --lint
    uv run pytest tests/
