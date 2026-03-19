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
