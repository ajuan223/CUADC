## MODIFIED Requirements

### Requirement: FieldProfile data model
The system SHALL define `FieldProfile(BaseModel)` with fields that describe field facts and mission constraints rather than hand-authored mission geometry. It SHALL include `name` (str), `description` (str), `coordinate_system` (str), `boundary` (BoundaryConfig), `landing` (LandingConfig), scan-constraint configuration sufficient for procedural scan generation, `loiter_point` (LoiterPointConfig), `safety_buffer_m` (float), and `attack_run` (AttackRunConfig).

#### Scenario: Load valid field JSON with procedural scan config
- **WHEN** `load_field_profile("sitl_default")` is called and the field JSON contains the scan-constraint section required for procedural scan generation
- **THEN** a `FieldProfile` instance is returned with those scan constraints populated
- **AND** no hand-authored scan waypoint list is required

#### Scenario: Missing field file
- **WHEN** `load_field_profile("nonexistent")` is called and `data/fields/nonexistent/field.json` does not exist
- **THEN** a `ConfigError` is raised indicating the field file was not found

#### Scenario: Invalid field JSON
- **WHEN** a field JSON file contains invalid data (e.g., `boundary.polygon` is not an array)
- **THEN** pydantic `ValidationError` is raised

---

### Requirement: Landing approach and touchdown must be inside geofence
The system SHALL validate that the landing touchdown point is inside the boundary polygon, and it SHALL validate that the procedurally derived landing approach waypoint is also inside the boundary polygon before mission generation succeeds.

#### Scenario: Landing points inside fence
- **WHEN** the touchdown point is inside the boundary polygon and the procedurally derived approach point is also inside the boundary polygon
- **THEN** field loading and landing geometry generation succeed without error

#### Scenario: Touchdown outside fence is rejected
- **WHEN** the touchdown point is outside the boundary polygon
- **THEN** `load_field_profile()` raises `FieldValidationError`

#### Scenario: Derived approach outside fence is rejected
- **WHEN** the touchdown point is valid but the procedurally derived approach point would be outside the boundary polygon
- **THEN** landing geometry generation SHALL fail with a validation error instead of relying on a user-authored fallback coordinate
