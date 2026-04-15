## ADDED Requirements

### Requirement: FieldProfile data model
The system SHALL define `FieldProfile(BaseModel)` with fields: `name` (str), `description` (str), `coordinate_system` (str), `boundary` (BoundaryConfig), `landing` (LandingConfig), `scan_waypoints` (ScanWaypointsConfig), `loiter_point` (LoiterPointConfig), `safety_buffer_m` (float).

#### Scenario: Load valid field JSON
- **WHEN** `load_field_profile("sitl_default")` is called and `data/fields/sitl_default/field.json` exists and is valid
- **THEN** a `FieldProfile` instance is returned with all fields populated from the JSON

#### Scenario: Missing field file
- **WHEN** `load_field_profile("nonexistent")` is called and `data/fields/nonexistent/field.json` does not exist
- **THEN** a `ConfigError` is raised indicating the field file was not found

#### Scenario: Invalid field JSON
- **WHEN** a field JSON file contains invalid data (e.g., `boundary.polygon` is not an array)
- **THEN** pydantic `ValidationError` is raised

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

### Requirement: Loiter point must be inside geofence
The system SHALL validate that the loiter point is inside the boundary polygon.

#### Scenario: Loiter point inside fence
- **WHEN** the loiter point is inside the boundary polygon
- **THEN** `load_field_profile()` succeeds without error

#### Scenario: Loiter point outside fence is rejected
- **WHEN** the loiter point is outside the boundary polygon
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
