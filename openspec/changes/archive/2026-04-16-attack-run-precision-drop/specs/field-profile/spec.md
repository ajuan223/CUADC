## MODIFIED Requirements

### Requirement: FieldProfile data model
The system SHALL define `FieldProfile(BaseModel)` with fields: `name` (str), `description` (str), `coordinate_system` (str), `boundary` (BoundaryConfig), `landing` (LandingConfig), `scan_waypoints` (ScanWaypointsConfig), `loiter_point` (LoiterPointConfig), `safety_buffer_m` (float), `attack_run` (AttackRunConfig).

#### Scenario: Load valid field JSON with attack_run config
- **WHEN** `load_field_profile("sitl_default")` is called and the field JSON contains an `attack_run` section
- **THEN** a `FieldProfile` instance is returned with `attack_run` populated from the JSON

#### Scenario: Load field JSON without attack_run config (backward compatible)
- **WHEN** a field JSON does not contain an `attack_run` section
- **THEN** `FieldProfile.attack_run` SHALL use default values (approach_distance_m=200, exit_distance_m=200, release_acceptance_radius_m=0)

#### Scenario: Missing field file
- **WHEN** `load_field_profile("nonexistent")` is called and `data/fields/nonexistent/field.json` does not exist
- **THEN** a `ConfigError` is raised indicating the field file was not found

#### Scenario: Invalid field JSON
- **WHEN** a field JSON file contains invalid data (e.g., `boundary.polygon` is not an array)
- **THEN** pydantic `ValidationError` is raised

---

## ADDED Requirements

### Requirement: AttackRunConfig data model
The system SHALL define `AttackRunConfig(BaseModel)` with fields: `approach_distance_m` (float, default 200), `exit_distance_m` (float, default 200), `release_acceptance_radius_m` (float, default 0). These parameters control the attack run geometry and waypoint acceptance radius.

#### Scenario: Default values when not specified
- **WHEN** an `attack_run` section is absent from field JSON
- **THEN** `AttackRunConfig` SHALL use defaults: `approach_distance_m=200`, `exit_distance_m=200`, `release_acceptance_radius_m=0`

#### Scenario: Custom attack run distances
- **WHEN** a field JSON specifies `"attack_run": {"approach_distance_m": 300, "exit_distance_m": 150}`
- **THEN** the loaded `AttackRunConfig` SHALL have those exact values
