## MODIFIED Requirements

### Requirement: Amount conversion to cents
The system SHALL convert decimal dollar amounts to integer cents using `int(round(amount * 100))` to avoid floating-point truncation errors.

#### Scenario: Amount with floating-point representation issue
- **WHEN** a CSV contains an amount of `19.99`
- **THEN** the system SHALL store `1999` cents (not `1998` from truncation)

#### Scenario: Exact cent amounts
- **WHEN** a CSV contains an amount of `10.00`
- **THEN** the system SHALL store `1000` cents

### Requirement: Duplicate detection scoped to internal account
The system SHALL use `(date, amount_cents, raw_description, internal_account)` as the dedup key. The database count query for existing duplicates SHALL also filter by `internal_id`.

#### Scenario: Same transaction on different accounts
- **WHEN** a user imports a CSV with a `$50.00 Amazon` charge on `2026-03-15` for `Checking`
- **AND** a prior import already has a `$50.00 Amazon` charge on `2026-03-15` for `Credit Card`
- **THEN** the system SHALL insert the new transaction (different internal account = not a duplicate)

#### Scenario: Same transaction on same account
- **WHEN** a user imports a CSV with a `$50.00 Amazon` charge on `2026-03-15` for `Checking`
- **AND** a prior import already has a `$50.00 Amazon` charge on `2026-03-15` for `Checking`
- **THEN** the system SHALL skip the duplicate

### Requirement: Upload error display
The system SHALL NOT render raw exception messages as unescaped HTML. Error messages from CSV parsing failures SHALL be HTML-escaped before display.

#### Scenario: CSV with special characters in error
- **WHEN** a CSV parsing error contains HTML-like content (e.g., angle brackets)
- **THEN** the error message SHALL be displayed as escaped text, not rendered as HTML
