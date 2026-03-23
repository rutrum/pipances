## REMOVED Requirements

### Requirement: Transactions page displays approved transactions
**Reason**: Transaction table absorbed into the Explore page (with charts) and the Data page (standalone table in phase 2).
**Migration**: Use `/explore` for chart+table view, or `/data/transactions` (phase 2) for table-only view.

### Requirement: Date range filtering with presets
**Reason**: Absorbed into Explore page date range controls.
**Migration**: Use `/explore` date range presets.

### Requirement: Column sorting
**Reason**: Absorbed into Explore page transaction table.
**Migration**: Use `/explore` table sorting.

### Requirement: Account column filtering
**Reason**: Absorbed into Explore page filter dropdowns.
**Migration**: Use `/explore` filter dropdowns.

### Requirement: Pagination
**Reason**: Absorbed into Explore page transaction table.
**Migration**: Use `/explore` pagination controls.

### Requirement: Filter transactions by category
**Reason**: Absorbed into Explore page category filter dropdown.
**Migration**: Use `/explore?category=X`.

### Requirement: Category displayed in transaction table
**Reason**: Absorbed into Explore page transaction table.
**Migration**: Category column displayed in `/explore` table.

### Requirement: Filter state persists on page refresh
**Reason**: Absorbed into Explore page deep linking.
**Migration**: Use `/explore` URL query parameters.

### Requirement: Amount display format
**Reason**: Absorbed into Explore page transaction table.
**Migration**: Same formatting applied in `/explore` table.

### Requirement: Query parameter validation
**Reason**: Absorbed into Explore page.
**Migration**: Same validation applied in `/explore` route.

### Requirement: Date filter validation
**Reason**: Absorbed into Explore page.
**Migration**: Same validation applied in `/explore` route.

### Requirement: Custom date range inline layout
**Reason**: Absorbed into Explore page.
**Migration**: Same layout in `/explore` date range controls.

### Requirement: Server-side rendering via HTMX
**Reason**: Absorbed into Explore page.
**Migration**: Same HTMX pattern in `/explore`.
