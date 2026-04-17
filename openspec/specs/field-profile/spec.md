## ADDED Requirements

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

---

### Requirement: Geofence polygon must be closed
The system SHALL validate that the boundary polygon is closed — the first and last coordinate points MUST be equal, or the system SHALL auto-close the polygon by appending the first point.

#### Scenario: Auto-close open polygon
- **WHEN** a field JSON has a polygon with 4 distinct vertices (first != last)
- **THEN** the loaded `FieldProfile` boundary polygon has 5 vertices (first == last)

#### Scenario: Already closed polygon passes validation
- **WHEN** a field JSON has a polygon with 5 vertices where first == last
- **THEN** the loaded `FieldProfile` boundary polygon retains those 5 vertices unchanged

---

### Requirement: Scan waypoints must be inside geofence
The system SHALL validate that all scan waypoints are inside the boundary polygon. Waypoints outside the geofence SHALL cause a `FieldValidationError` with the offending waypoint index.

#### Scenario: All waypoints inside fence
- **WHEN** all scan waypoints in a field JSON are inside the boundary polygon
- **THEN** `load_field_profile()` succeeds without error

#### Scenario: Waypoint outside fence is rejected
- **WHEN** a scan waypoint is outside the boundary polygon
- **THEN** `load_field_profile()` raises `FieldValidationError` indicating which waypoint is outside

---

### Requirement: Landing approach and touchdown must be inside geofence
The system SHALL validate that the landing approach waypoint and touchdown point are inside the boundary polygon.

#### Scenario: Landing points inside fence
- **WHEN** both approach_waypoint and touchdown_point are inside the boundary polygon
- **THEN** `load_field_profile()` succeeds without error

#### Scenario: Touchdown outside fence is rejected
- **WHEN** the touchdown point is outside the boundary polygon
- **THEN** `load_field_profile()` raises `FieldValidationError`

---

### Requirement: Safety buffer must be positive
The system SHALL validate that `safety_buffer_m` is greater than zero.

#### Scenario: Negative safety buffer is rejected
- **WHEN** `safety_buffer_m` is set to `-10.0`
- **THEN** pydantic validation raises `ValidationError`

#### Scenario: Zero safety buffer is rejected
- **WHEN** `safety_buffer_m` is set to `0.0`
- **THEN** pydantic validation raises `ValidationError`

---

### Requirement: Point-in-polygon uses ray casting algorithm
The system SHALL implement point-in-polygon detection using the ray casting algorithm. The function SHALL accept a (lat, lon) point and a list of (lat, lon) polygon vertices.

#### Scenario: Point inside polygon
- **WHEN** a point known to be inside a square polygon is tested
- **THEN** `point_in_polygon()` returns `True`

#### Scenario: Point outside polygon
- **WHEN** a point known to be outside a square polygon is tested
- **THEN** `point_in_polygon()` returns `False`

#### Scenario: Point on polygon edge
- **WHEN** a point exactly on a polygon edge is tested
- **THEN** `point_in_polygon()` returns `True`

### Requirement: AttackRunConfig data model
The system SHALL define `AttackRunConfig(BaseModel)` with fields: `approach_distance_m` (float, default 200), `exit_distance_m` (float, default 200), `release_acceptance_radius_m` (float, default 0). These parameters control the attack run geometry and waypoint acceptance radius.

#### Scenario: Default values when not specified
- **WHEN** an `attack_run` section is absent from field JSON
- **THEN** `AttackRunConfig` SHALL use defaults: `approach_distance_m=200`, `exit_distance_m=200`, `release_acceptance_radius_m=0`

#### Scenario: Custom attack run distances
- **WHEN** a field JSON specifies `"attack_run": {"approach_distance_m": 300, "exit_distance_m": 150}`
- **THEN** the loaded `AttackRunConfig` SHALL have those exact values
