## 1. Nix Flake Updates

- [x] 1.1 Add DaisyUI CSS as a flake input (jsDelivr URL for daisyui@5/daisyui.css)
- [x] 1.2 Add shell hook that symlinks the DaisyUI CSS flake input to `./daisyui.css` in the project root
- [x] 1.3 Add `daisyui.css` and compiled CSS output to `.gitignore`

## 2. Tailwind Build Pipeline

- [x] 2.1 Create `input.css` at project root with `@import "tailwindcss"`, `@import "./daisyui.css"`, and `@source` pointing to templates
- [x] 2.2 Build with `tailwindcss -i input.css -o static/css/style.css` and verify DaisyUI classes compile

## 3. FastAPI App

- [x] 3.1 Create `src/financial_pipeline/main.py` with FastAPI app, Jinja2 template config, static file mount (from project root `static/`), index route, and uvicorn `__main__` runner
- [x] 3.2 Create `src/financial_pipeline/templates/base.html` — base Jinja2 template with HTMX CDN script and link to compiled Tailwind CSS
- [x] 3.3 Create `src/financial_pipeline/templates/index.html` — extends base, renders a styled hello-world page using DaisyUI components

## 4. Verification

- [x] 4.1 Run `uv run python -m financial_pipeline.main` and verify the index page renders with DaisyUI styling
