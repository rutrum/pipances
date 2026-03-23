## REMOVED Requirements

### Requirement: Dashboard time range filter
**Reason**: Dashboard functionality absorbed into the Explore page, which has its own date range and filter controls.
**Migration**: Use `/explore` with date range presets instead of `/dashboard`.

### Requirement: Dashboard tab navigation
**Reason**: Dashboard tabs (Summary, Categories, By Account) replaced by the unified Explore page with filter dropdowns.
**Migration**: Use `/explore` filter dropdowns to scope by category or account.

### Requirement: Tab content loaded via HTMX partials
**Reason**: Dashboard tab endpoints replaced by single Explore endpoint.
**Migration**: Use `/explore` endpoint.

### Requirement: Dashboard displays summary statistics
**Reason**: Summary stats now displayed on the Explore page, scoped to current filters.
**Migration**: Use `/explore` — stats are always visible.

### Requirement: Category spending pie chart
**Reason**: Replaced by uniform chart set on Explore page.
**Migration**: Use `/explore?category=X` to see spending for a specific category.

### Requirement: Category drill-down selector
**Reason**: Replaced by Explore filter dropdowns.
**Migration**: Use `/explore?category=X` for category drill-down.

### Requirement: Category drill-down content
**Reason**: Replaced by Explore page filtered view.
**Migration**: Use `/explore?category=X` to see income/expenses and transactions for a category.

### Requirement: Account selector
**Reason**: Replaced by Explore internal account filter dropdown.
**Migration**: Use `/explore?internal=X` for account drill-down.

### Requirement: Account balance at end of period
**Reason**: Account-specific balance calculation dropped in favor of uniform chart set.
**Migration**: No direct replacement. May revisit later.

### Requirement: Account income, expenses, and net
**Reason**: Replaced by Explore summary stats filtered to an account.
**Migration**: Use `/explore?internal=X` — stats show income/expenses/net for that account.

### Requirement: Account monthly trend chart
**Reason**: Replaced by uniform monthly income/expenses chart on Explore.
**Migration**: Use `/explore?internal=X` — monthly chart shows data for that account.

### Requirement: Account top external accounts chart
**Reason**: Replaced by uniform top expenses chart on Explore.
**Migration**: Use `/explore?internal=X` — top expenses chart shows data for that account.

### Requirement: Monthly income vs expenses chart
**Reason**: Moved to Explore page.
**Migration**: Use `/explore` — chart is always displayed.

### Requirement: Top expenses by external account chart
**Reason**: Moved to Explore page.
**Migration**: Use `/explore` — chart is always displayed.

### Requirement: Weekly spending trend chart
**Reason**: Moved to Explore page.
**Migration**: Use `/explore` — chart is always displayed.

### Requirement: Charts computed server-side with Polars
**Reason**: Moved to Explore page.
**Migration**: Same implementation, now served from `/explore` route.
