## ADDED Requirements

### Requirement: Vision global variable SHALL provide thread-safe drop point access
The system SHALL define a module-level global variable `VISION_DROP_POINT` in `striker/vision/global_var.py` with thread-safe accessor functions.

#### Scenario: Set drop point from vision program
- **WHEN** the vision program calls `set_vision_drop_point(30.261, 120.095)`
- **THEN** `VISION_DROP_POINT` SHALL be set to `(30.261, 120.095)` under lock protection

#### Scenario: Read drop point from Striker
- **WHEN** Striker calls `get_vision_drop_point()`
- **AND** the vision program has set `(30.261, 120.095)`
- **THEN** the function SHALL return `(30.261, 120.095)` under lock protection

#### Scenario: Read when no drop point set
- **WHEN** Striker calls `get_vision_drop_point()`
- **AND** no vision program has called `set_vision_drop_point()`
- **THEN** the function SHALL return `None`

### Requirement: Vision global variable SHALL validate GPS coordinates
The system SHALL validate that set coordinates are within valid GPS ranges before storing.

#### Scenario: Reject invalid latitude
- **WHEN** `set_vision_drop_point(91.0, 120.0)` is called
- **THEN** the system SHALL raise `ValueError`
- **AND** `VISION_DROP_POINT` SHALL remain unchanged

#### Scenario: Reject invalid longitude
- **WHEN** `set_vision_drop_point(30.0, 181.0)` is called
- **THEN** the system SHALL raise `ValueError`
- **AND** `VISION_DROP_POINT` SHALL remain unchanged
