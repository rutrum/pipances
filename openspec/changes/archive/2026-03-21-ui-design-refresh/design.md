## Context

The app uses FastAPI + Jinja2Templates with HTMX. Templates extend `base.html` and are rendered via `templates.TemplateResponse(request, "template.html", ctx)`. There is no middleware or shared context injection — each route handler manually builds its context dict. DaisyUI v5 is loaded via a CSS import, Tailwind v4 via standalone CLI.

## Goals / Non-Goals

**Goals:**
- Switch to `silk` theme for a warmer visual feel
- Make the navbar contextually aware (active page, icons, inbox count)
- Improve inbox placeholder styling
- Provide toast feedback after key user actions

**Non-Goals:**
- Dashboard visual improvements (deferred — high complexity, revisit when more features land)
- Theme switcher UI (just pick silk for now)
- Loading spinners / progress bars
- Footer or other structural layout changes

## Decisions

### 1. Shared template context via Jinja2 globals

**Decision**: Inject `active_page` and `inbox_count` into templates using Jinja2's `env.globals` with a callable, rather than modifying every route handler.

**Rationale**: FastAPI's Jinja2Templates exposes `env`. We can register a function that queries the inbox count lazily. However, since the count requires a DB session and is async, the simpler approach is a **Jinja2 context processor** pattern: a helper function called from each route that merges shared context into the route's dict.

**Alternative considered**: Starlette middleware that injects into `request.state`. Rejected because template context is separate from request state — we'd still need to manually unpack it in every route.

**Approach**: Create a `shared_context(request, active_page, session)` async helper in `main.py` that returns `{"active_page": active_page, "inbox_count": count}`. Each route handler merges this into its context dict via `ctx |= await shared_context(...)`.

### 2. Icons via Lucide CDN

**Decision**: Use Lucide icons via CDN script tag. Icons are placed as `<i data-lucide="icon-name"></i>` and initialized with `lucide.createIcons()`.

**Rationale**: The inline SVG Jinja macro approach (Heroicons) had rendering issues and was verbose. Lucide is lightweight (~80KB), has a clean stroke style that matches DaisyUI, and provides 1500+ icons for future use. The CDN dependency is acceptable since we already depend on CDN for HTMX and Vega.

**Alternative considered**: Inline SVG Jinja macro with Heroicons. Rejected due to rendering issues and template verbosity for a growing icon set.

### 3. Toast notifications via HTMX swap + auto-dismiss

**Decision**: Add a `#toast-container` div in `base.html`. Backend returns toast HTML via HTMX `HX-Trigger` response header with `afterSwap` event, or via OOB (out-of-band) swap. Toast auto-dismisses after a few seconds using a small inline script or CSS animation.

**Rationale**: DaisyUI's `toast` component is just positioned `div.toast > div.alert`. Combined with HTMX's `hx-swap-oob`, the backend can inject a toast into the container from any response. Auto-dismiss avoids toast pile-up.

**Approach**:
- `base.html` gets a `<div id="toast-container" class="toast toast-end toast-bottom"></div>`
- For redirect flows (upload → inbox): use a query param `?toast=upload_success` and render the toast server-side on inbox page load
- For in-page actions (commit): return toast HTML as OOB swap in the HTMX response

### 4. Active page indicator

**Decision**: Pass `active_page` string (e.g., `"upload"`, `"inbox"`) from each route. The `_navbar.html` template conditionally applies `font-bold border-b-2 border-primary text-primary` classes on the matching menu link.

**Rationale**: DaisyUI's built-in `active` class on `menu` items produced no visible effect with the `silk` theme in horizontal menus. Explicit Tailwind utility classes (bold text, primary color, bottom border) give a clear, theme-independent active indicator.

### 5. Inbox badge live update on commit

**Decision**: After a commit action, the HTMX response includes an OOB swap targeting the inbox badge element, updating the count without a full page reload.

**Rationale**: Without this, the badge shows a stale count after committing transactions until the user navigates to another page. The OOB swap keeps the badge accurate in real-time.

## Risks / Trade-offs

- **`silk` theme may affect chart readability** → Verify Altair chart colors still contrast well against the silk background. Mitigate by checking dashboard after theme switch.
- **shared_context adds a DB query per page load** → The inbox count query is trivial (COUNT with WHERE). Acceptable overhead for a single-user app.
- **Toast auto-dismiss timing** → If too fast, user misses feedback. Start with 4 seconds, adjust based on feel.
