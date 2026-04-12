## REMOVED Requirements

### Requirement: Inline editing of transaction description
The user SHALL be able to edit a transaction's description directly in the inbox table by clicking on the cell.

**Reason**: Replaced by modal-based editing for improved UX and maintainability. Inline editing scattered across three fields made form interactions complex and difficult to extend.

**Migration**: Users now click an Edit button on each row to open a modal form containing all editable fields (description, external account, category) in a cohesive interface.

#### Scenario: Edit description
- **WHEN** user clicks on a transaction's description cell in the inbox
- **THEN** the cell SHALL become an editable text input with ghost styling (borderless until focused)
- **WHEN** user submits the edit (blur or enter)
- **THEN** the system SHALL save the new description to the database via HTMX PATCH
- **THEN** the cell SHALL update to show the new value without full page reload

#### Scenario: Empty description placeholder
- **WHEN** a transaction has no description set
- **THEN** the description cell SHALL display italic grey text reading "click to edit"
- **THEN** the placeholder SHALL be visually distinct from actual description text
- **THEN** the placeholder SHALL have no extra padding and align with populated field values

#### Scenario: Editing an ML-suggested description clears confidence
- **WHEN** user edits a transaction's description that was ML-suggested
- **THEN** `ml_confidence_description` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the description field

### Requirement: Inline editing of external account
The user SHALL be able to edit a transaction's external account using the combo box component with search and inline creation.

**Reason**: Replaced by modal-based editing. Inline combo box in table cells made layout complex and difficult to manage focus/dropdown overflow.

**Migration**: Users now access the external account field through the modal edit form, which provides better visual hierarchy and space for dropdown results.

#### Scenario: Edit external account
- **WHEN** user clicks on a transaction's external account cell in the inbox
- **THEN** a combo box SHALL appear with ghost-styled input (borderless until focused) showing matching external accounts as the user types
- **THEN** the user SHALL be able to select an existing account or create a new one
- **WHEN** user selects or creates an account
- **THEN** the system SHALL resolve or create the external account in the database
- **THEN** the system SHALL update the transaction's external_id
- **THEN** the cell SHALL update without full page reload

#### Scenario: Editing an ML-suggested external account clears confidence
- **WHEN** user edits a transaction's external account that was ML-suggested
- **THEN** `ml_confidence_external` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the external account field

### Requirement: Inline category editing via combo box
The user SHALL be able to assign or change a transaction's category using the combo box component.

**Reason**: Replaced by modal-based editing for consistency with other field edits.

**Migration**: Users now access category selection through the modal edit form alongside description and external account fields.

#### Scenario: Assign category to transaction
- **WHEN** user clicks on a transaction's category cell in the inbox
- **THEN** a combo box SHALL appear with ghost-styled input (borderless until focused) allowing search and selection of existing categories or creation of a new one
- **WHEN** user selects or creates a category
- **THEN** the transaction's category SHALL be updated
- **THEN** the row SHALL re-render without a full page reload

#### Scenario: Editing an ML-suggested category clears confidence
- **WHEN** user edits a transaction's category that was ML-suggested
- **THEN** `ml_confidence_category` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the category field

## ADDED Requirements

### Requirement: User can open edit modal for inbox transaction
The system SHALL display an Edit button on each inbox transaction row that opens a modal form for editing that transaction's details.

#### Scenario: Edit button opens modal
- **WHEN** user clicks the Edit button on an inbox transaction row
- **THEN** a modal dialog appears containing the transaction edit form with current values pre-filled

#### Scenario: Modal displays transaction context
- **WHEN** modal is open
- **THEN** it shows read-only transaction context (date, amount, raw description) and editable fields (description, external account, category)

### Requirement: User can edit transaction description via modal
The system SHALL allow the user to modify the transaction description field within the modal, persisting changes immediately.

#### Scenario: Edit description and blur
- **WHEN** user modifies the description text input and blurs the field
- **THEN** the system sends PATCH to `/transactions/{id}` with the new description value
- **AND** the description field updates with the new value (or error if applicable)

#### Scenario: Edit description with empty value
- **WHEN** user clears the description field and blurs
- **THEN** the system persists the empty value
- **AND** the field remains editable
- **AND** the transaction cannot be approved until description is filled

### Requirement: User can edit transaction external account via modal
The system SHALL allow the user to modify the transaction external account via a select dropdown in the modal, persisting changes immediately.

#### Scenario: Change external account dropdown
- **WHEN** user selects a different value from the external account dropdown
- **THEN** the system sends PATCH to `/transactions/{id}` with the new external account value
- **AND** the dropdown updates with the new value (or error if applicable)

#### Scenario: Clear external account
- **WHEN** user selects empty/null option from external dropdown
- **THEN** the system persists the empty external account
- **AND** the field remains editable

### Requirement: User can edit transaction category via modal
The system SHALL allow the user to modify the transaction category via a select dropdown in the modal, persisting changes immediately.

#### Scenario: Change category dropdown
- **WHEN** user selects a different value from the category dropdown
- **THEN** the system sends PATCH to `/transactions/{id}` with the new category value
- **AND** the dropdown updates with the new value (or error if applicable)

#### Scenario: Clear category
- **WHEN** user selects empty/null option from category dropdown
- **THEN** the system persists the empty category
- **AND** the field remains editable

### Requirement: Modal closes and row refreshes
The system SHALL refresh the transaction row in the inbox table after the modal is closed.

#### Scenario: Close modal via button
- **WHEN** user clicks the close button (X) on the modal
- **THEN** the modal closes
- **AND** the system fetches the updated transaction data and refreshes the row in the table

#### Scenario: Close modal via escape key
- **WHEN** user presses Escape key while modal is open
- **THEN** the modal closes
- **AND** the system fetches the updated transaction data and refreshes the row in the table

### Requirement: Approve button remains separate in modal
The system SHALL provide an Approve button within the modal that allows the user to mark the transaction for approval, as a separate intentional action from field edits.

#### Scenario: Approve transaction via modal
- **WHEN** transaction has all required fields filled (description is not empty)
- **AND** user clicks the Approve button in the modal
- **THEN** the system marks the transaction as `marked_for_approval`
- **AND** the button changes to show approved state
- **AND** the row refreshes to reflect the approval status

#### Scenario: Approve button disabled for incomplete transaction
- **WHEN** transaction is missing required fields (description is empty)
- **THEN** the Approve button is disabled and non-clickable

### Requirement: Modal field errors display inline
The system SHALL display validation errors next to the affected field without closing the modal.

#### Scenario: Field validation error
- **WHEN** PATCH to `/transactions/{id}` returns validation error (422 status)
- **THEN** the modal remains open
- **AND** error message appears next to the affected field
- **AND** user can correct and retry

### Requirement: Inbox row template simplified for modal editing
The system SHALL remove inline click-to-edit functionality from the inbox row table, replacing it with the modal-based Edit button.

#### Scenario: Row displays fields without inline editing
- **WHEN** inbox table renders
- **THEN** each row shows transaction data (description, category, external) as read-only text
- **AND** a single Edit button is present
- **AND** clicking any field directly does not trigger edit mode
