## MODIFIED Requirements

### Requirement: Drop point decision moves to LOITER_HOLD state
Drop point resolution previously occurred in ScanState upon scan completion. It SHALL now occur in LoiterHoldState when the aircraft enters the preburned LOITER_UNLIM.

#### Scenario: Drop point resolved in LOITER_HOLD
- **WHEN** the aircraft enters LOITER_UNLIM
- **THEN** LoiterHoldState SHALL read the vision global variable for drop point
- **AND** fall back to `field_profile.attack_run.fallback_drop_point` if vision unavailable

### Requirement: Drop point source from vision global variable
The drop point SHALL be read from the in-process Python global variable `VISION_DROP_POINT` instead of from the `DropPointTracker` median filter.

#### Scenario: Vision drop point via global variable
- **WHEN** `VISION_DROP_POINT` is set to `(30.261, 120.095)`
- **THEN** the system SHALL use this as the active drop point with source `"vision"`

#### Scenario: Fallback from field profile
- **WHEN** `VISION_DROP_POINT` is None
- **THEN** the system SHALL use `field_profile.attack_run.fallback_drop_point` with source `"fallback_field"`
