## Delta

### New Requirement: ML-suggested fields are visually distinguished
The inbox SHALL visually indicate which field values were suggested by the ML model, on a per-field basis.

#### Scenario: ML-suggested field display
- **WHEN** a transaction field has a non-null `ml_confidence_*` value
- **THEN** the field SHALL be visually distinguished from human-set fields (e.g. colored background, badge, or other DaisyUI styling)
- **THEN** the visual indicator SHALL be per-field (not per-row)

#### Scenario: Human-set field display
- **WHEN** a transaction field has a null `ml_confidence_*` value
- **THEN** the field SHALL display with normal styling (no ML indicator)

### Modified Requirement: Inline editing of transaction description

#### Scenario: Editing an ML-suggested description clears confidence
- **WHEN** user edits a transaction's description that was ML-suggested
- **THEN** `ml_confidence_description` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the description field

### Modified Requirement: Inline editing of external account

#### Scenario: Editing an ML-suggested external account clears confidence
- **WHEN** user edits a transaction's external account that was ML-suggested
- **THEN** `ml_confidence_external` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the external account field

### Modified Requirement: Inline category editing via combo box

#### Scenario: Editing an ML-suggested category clears confidence
- **WHEN** user edits a transaction's category that was ML-suggested
- **THEN** `ml_confidence_category` SHALL be set to `None`
- **THEN** the ML visual indicator SHALL disappear from the category field
