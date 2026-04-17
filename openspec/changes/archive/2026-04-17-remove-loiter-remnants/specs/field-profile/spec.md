## MODIFIED Requirements

### Requirement: FieldProfile data model
The system SHALL define `FieldProfile(BaseModel)` with fields: `name` (str), `description` (str), `coordinate_system` (str), `boundary` (BoundaryConfig), `landing` (LandingConfig), `scan` (ScanConfig), `attack_run` (AttackRunConfig), and `safety_buffer_m` (float).

`LandingConfig` SHALL include an optional `use_do_land_start` field (bool, default `True`). When `True`, the landing sequence generator SHALL produce DO_LAND_START + approach + NAV_LAND (3 items). When `False`, it SHALL produce approach (NAV_WAYPOINT) + NAV_LAND (2 items).

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

#### Scenario: Load valid field JSON with default landing config
- **WHEN** `load_field_profile()` is called with a field JSON that omits `landing.use_do_land_start`
- **THEN** `field_profile.landing.use_do_land_start` returns `True` (default)

#### Scenario: SITL field sets use_do_land_start to false
- **WHEN** `load_field_profile("sitl_default")` is called and `data/fields/sitl_default/field.json` contains `"use_do_land_start": false`
- **THEN** `field_profile.landing.use_do_land_start` returns `False` and landing sequence produces 2 items (NAV_WAYPOINT + NAV_LAND)

#### Scenario: Real field uses DO_LAND_START by default
- **WHEN** `load_field_profile("zijingang")` is called and the field JSON does not specify `use_do_land_start`
- **THEN** `field_profile.landing.use_do_land_start` returns `True` and landing sequence produces 3 items (DO_LAND_START + approach + NAV_LAND)

### Requirement: Safety buffer must be positive
The system SHALL validate that `safety_buffer_m` is greater than zero.

#### Scenario: Negative safety buffer is rejected
- **WHEN** `safety_buffer_m` is set to `-10.0`
- **THEN** pydantic validation raises `ValidationError`

#### Scenario: Zero safety buffer is rejected
- **WHEN** `safety_buffer_m` is set to `0.0`
- **THEN** pydantic validation raises `ValidationError`

## REMOVED Requirements

### Requirement: Loiter point must be inside geofence
**Reason**: The standard mission flow no longer includes a loiter waiting phase, so the active field schema must not require a loiter point.
**Migration**: Remove `loiter_point` from active `field.json` files, editor import/export payloads, and related validation tests. Keep only landing, scan, attack-run, and safety fields.
