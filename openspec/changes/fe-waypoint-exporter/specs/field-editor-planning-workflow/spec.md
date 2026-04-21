## MODIFIED Requirements

### Requirement: Export toolbar provides multiple export options
The planning panel export area SHALL display three export buttons instead of a single "导出" button:
1. "导出航点 (.waypoints)" — generates QGC WPL 110 waypoint file
2. "导出围栏 (.poly)" — generates geofence polygon file
3. "导出配置 (field.json)" — generates the existing field.json config

Each button SHALL be independently enabled/disabled based on validation state:
- `.waypoints` export: disabled when blocking errors exist
- `.poly` export: disabled when boundary polygon has < 3 distinct vertices
- `field.json` export: disabled when blocking errors exist (unchanged behavior)

#### Scenario: All exports available
- **WHEN** field profile passes validation with 3+ boundary vertices
- **THEN** all three export buttons SHALL be enabled

#### Scenario: No boundary prevents poly export
- **WHEN** boundary polygon has fewer than 3 distinct vertices
- **THEN** the ".poly" export button SHALL be disabled; ".waypoints" and "field.json" buttons follow their own validation rules

#### Scenario: Blocking errors disable waypoint and json export
- **WHEN** validation has blocking errors
- **THEN** ".waypoints" and "field.json" export buttons SHALL be disabled

### Requirement: Download file supports multiple MIME types
The `downloadFile()` function SHALL accept an optional MIME type parameter, defaulting to `application/json`. For `.waypoints` and `.poly` files it SHALL use `text/plain`.

#### Scenario: Waypoint file download
- **WHEN** downloading a `.waypoints` file
- **THEN** the blob SHALL use MIME type `text/plain`

#### Scenario: JSON file download
- **WHEN** downloading a `field.json` file
- **THEN** the blob SHALL use MIME type `application/json` (default)
