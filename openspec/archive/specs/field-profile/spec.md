## MODIFIED Requirements

### Requirement: FieldProfile data model
The system SHALL define `FieldProfile(BaseModel)` with fields that describe strictly field facts and runtime mission constraints rather than hand-authored mission geometry or planning parameters. It SHALL include `name` (str), `description` (str), `coordinate_system` (str), `boundary` (BoundaryConfig), `landing` (LandingConfig, containing ONLY `touchdown_point` and `heading_deg`), `scan` (ScanConfig, containing ONLY `altitude_m`), `safety_buffer_m` (float), and `attack_run` (AttackRunConfig). All procedural generation parameters (spacing, glide slope, etc.) MUST be removed from this model.

#### Scenario: Load valid field JSON with runtime config
- **WHEN** `load_field_profile("sitl_default")` is called
- **THEN** a `FieldProfile` instance is returned with strictly runtime constraints populated
- **AND** the instance MUST NOT contain any legacy planning fields (such as `scan.spacing_m` or `landing.glide_slope_deg`)

#### Scenario: Missing field file
- **WHEN** `load_field_profile("nonexistent")` is called and `data/fields/nonexistent/field.json` does not exist
- **THEN** a `ConfigError` is raised indicating the field file was not found

#### Scenario: Invalid field JSON
- **WHEN** a field JSON file contains invalid data (e.g., `boundary.polygon` is not an array)
- **THEN** pydantic `ValidationError` is raised

### Requirement: Landing approach and touchdown must be inside geofence
The system SHALL validate that the landing touchdown point is inside the boundary polygon. Validation of the procedurally derived landing approach waypoint SHALL be decoupled from `load_field_profile()` and instead performed during the planning phase in the Field Editor, since `FieldProfile` no longer contains the parameters to calculate the approach.

#### Scenario: Landing points inside fence
- **WHEN** the touchdown point is inside the boundary polygon
- **THEN** field loading succeeds without error

#### Scenario: Touchdown outside fence is rejected
- **WHEN** the touchdown point is outside the boundary polygon
- **THEN** `load_field_profile()` raises `FieldValidationError`
