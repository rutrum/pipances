## Context

The app has a transactions table with approved records. We want a dashboard page that surfaces summary statistics and charts from all approved transactions. The tech stack specifies Polars for data processing and Altair for visualization (Vega-Lite).

## Goals / Non-Goals

**Goals:**
- At-a-glance summary stats (income, expenses, net, net total)
- Three charts: monthly income vs expenses, top expenses by external account, weekly spending trend
- Server-side computation with Polars, client-side chart rendering via Vega-Embed
- Clean, responsive layout using DaisyUI components

**Non-Goals:**
- Date range filtering on the dashboard (deferred — show all approved transactions)
- Interactive drill-downs from charts to transaction lists
- Categories/tags (not yet implemented — top expenses uses external account names)
- Real-time updates or auto-refresh

## Decisions

### Computation module: `charts.py`
**Choice:** New module at `src/financial_pipeline/charts.py` that takes a Polars DataFrame of transactions and returns summary stats (dict) and Altair chart specs (JSON strings).
**Why:** Keeps the route handler thin — query DB, load into DataFrame, call chart functions, pass to template. Separates data logic from web concerns. Easy to test in isolation.
**Alternative:** Inline computation in the route handler. Rejected — mixes concerns, harder to maintain as charts grow.

### Altair charts rendered via Vega-Embed CDN
**Choice:** Load Vega-Embed, Vega-Lite, and Vega via CDN `<script>` tags in the dashboard template. Each chart is a `<div>` with an inline script calling `vegaEmbed('#chart-id', spec)`.
**Why:** Zero build step. Altair's output is a Vega-Lite JSON spec — Vega-Embed is the standard way to render it in a browser. CDN keeps it simple (self-hosting deferred to TODO).
**Alternative:** Server-side rendering to SVG/PNG. Rejected — loses interactivity (tooltips, zoom), adds server-side rendering complexity.

### Chart specs as JSON strings in template context
**Choice:** The `charts.py` module returns Altair chart specs as JSON strings. The template embeds them directly into inline `<script>` blocks via `{{ spec | safe }}`.
**Why:** Simple data flow. No need to serialize/deserialize on the frontend. Altair's `.to_json()` produces exactly what Vega-Embed expects.

### Layout with DaisyUI stats + CSS grid
**Choice:** Summary cards use DaisyUI `stats` component (horizontal row). Charts use a 2-column CSS grid that stacks on mobile. Monthly bar chart spans full width; top expenses and weekly trend sit side by side.
**Why:** DaisyUI stats component is purpose-built for this. Grid provides responsive layout without custom CSS.

### Weekly spending trend uses ISO weeks
**Choice:** Group expenses by ISO week number for the weekly trend chart.
**Why:** Standard, well-defined week boundaries. Polars has native ISO week support via `.dt.week()`.

### Data flow

```
┌──────────┐     ┌───────────┐     ┌───────────┐     ┌──────────┐
│ SQLite   │────▶│ Polars DF │────▶│ charts.py │────▶│ Template │
│ (query)  │     │           │     │           │     │          │
│          │     │ approved  │     │ stats{}   │     │ stat     │
│          │     │ txns as   │     │ chart1 {} │     │ cards    │
│          │     │ DataFrame │     │ chart2 {} │     │ + vega   │
│          │     │           │     │ chart3 {} │     │ embeds   │
└──────────┘     └───────────┘     └───────────┘     └──────────┘
```

Route handler:
1. Query all approved transactions (with joined accounts)
2. Convert to Polars DataFrame (id, date, amount_cents, description, external_name, internal_name)
3. Call `compute_stats(df)` → dict with income, expenses, net, net_total
4. Call `monthly_income_expenses_chart(df)` → JSON string
5. Call `top_expenses_chart(df, n=10)` → JSON string
6. Call `weekly_spending_chart(df)` → JSON string
7. Pass all to template

## Risks / Trade-offs

- **[CDN dependency for chart rendering]** → Dashboard won't render charts offline. Mitigation: deferred TODO to self-host/embed CDN deps.
- **[All transactions loaded into memory]** → For personal finance this is fine (thousands of rows). If dataset grows very large, would need server-side aggregation in SQL first. Mitigation: not a concern at current scale.
- **[No date filtering]** → Charts may become less useful as data grows over years. Mitigation: can add date range widget later (reusable partial already exists).
