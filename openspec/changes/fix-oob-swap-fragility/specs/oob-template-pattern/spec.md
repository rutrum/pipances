## ADDED Requirements

### Requirement: Render a template with OOB swap markup

The system SHALL render a template with the `hx-swap-oob` attribute included when the `oob=True` parameter is passed to the template renderer.

#### Scenario: Render template with OOB enabled
- **WHEN** a route calls `render_template("partial.html", data=..., oob=True)`
- **THEN** the rendered HTML includes `hx-swap-oob="..."` attributes for elements marked with `{% if oob %}`

#### Scenario: Render same template without OOB for full page load
- **WHEN** a route calls `render_template("partial.html", data=...)` (no `oob` parameter)
- **THEN** the rendered HTML does NOT include `hx-swap-oob` attributes, enabling reuse for initial page loads

### Requirement: OOB template pattern for pagination

When rendering pagination for an HTMX response, the pagination `<div>` SHALL include `hx-swap-oob="outerHTML:#inbox-pagination"` attribute.

#### Scenario: Pagination renders with OOB in HTMX response
- **WHEN** an HTMX request triggers `/inbox` with filter changes
- **THEN** the response includes a pagination div with `id="inbox-pagination"` and `hx-swap-oob="outerHTML:#inbox-pagination"` 
- **AND** HTMX swaps this div in place of the existing `#inbox-pagination` element on the page

#### Scenario: Pagination renders without OOB for initial page load
- **WHEN** a user navigates to `/inbox` directly (full page load)
- **THEN** the pagination div has `id="inbox-pagination"` but no `hx-swap-oob` attribute

### Requirement: OOB template pattern for transaction rows

When rendering a transaction row for an HTMX update, the row `<tr>` SHALL include `hx-swap-oob="outerHTML"` attribute.

#### Scenario: Transaction row renders with OOB in bulk update
- **WHEN** a bulk update operation updates multiple transactions
- **THEN** the response includes a `<tr>` element with `id="txn-{id}"` and `hx-swap-oob="outerHTML"`
- **AND** HTMX swaps the row in place of the existing row with that ID

### Requirement: OOB template pattern for toast notifications

When rendering a toast notification for an HTMX response, the toast div SHALL include `hx-swap-oob="innerHTML:#toast-container"` attribute.

#### Scenario: Toast renders with OOB in commit response
- **WHEN** a user commits transactions and the response needs to show a notification
- **THEN** the response includes a toast div with `id="toast-container"`, `hx-swap-oob="innerHTML:#toast-container"`, and success/warning message
- **AND** HTMX swaps the toast content into the existing `#toast-container` on the page

### Requirement: OOB template pattern for badge updates

When rendering a badge count for an HTMX response, the badge span SHALL include `hx-swap-oob="innerHTML:#inbox-badge"` attribute.

#### Scenario: Badge renders with OOB after commit
- **WHEN** a user commits transactions and the remaining count changes
- **THEN** the response includes a badge span with `id="inbox-badge"`, `hx-swap-oob="innerHTML:#inbox-badge"`, and updated count
- **AND** HTMX swaps the badge content into the existing `#inbox-badge` on the page

### Requirement: OOB template pattern for date range updates

When rendering date range display for an HTMX response, the date range div SHALL include `hx-swap-oob="outerHTML:#explore-date-range"` attribute.

#### Scenario: Date range renders with OOB in explore filter
- **WHEN** an HTMX request changes the date range preset on the explore page
- **THEN** the response includes a date range div with `id="explore-date-range"` and `hx-swap-oob="outerHTML:#explore-date-range"`
- **AND** HTMX swaps this div in place of the existing `#explore-date-range` element
