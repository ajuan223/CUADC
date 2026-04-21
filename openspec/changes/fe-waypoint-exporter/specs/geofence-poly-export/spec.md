## ADDED Requirements

### Requirement: Generate Mission Planner geofence poly file
The system SHALL generate a `.poly` geofence file from the boundary polygon in the current field profile. The file format SHALL be compatible with Mission Planner's geofence import.

The `.poly` file format SHALL be:
- First line: vertex count (integer)
- Subsequent lines: `lat lon` pairs (space-separated, WGS84, one per line)
- The polygon SHALL be closed (last point equals first point)

#### Scenario: Successful geofence export
- **WHEN** user clicks "导出围栏" and boundary polygon has at least 3 distinct vertices
- **THEN** system SHALL generate and download a `.poly` file with the correct vertex count and WGS84 coordinates

#### Scenario: Insufficient boundary vertices
- **WHEN** boundary polygon has fewer than 3 distinct vertices
- **THEN** the geofence export button SHALL be disabled

### Requirement: All geofence coordinates in WGS84
Every latitude and longitude written to the `.poly` file SHALL be converted from GCJ-02 to WGS84 via `gcj02ToWgs84()`.

#### Scenario: Coordinate conversion for geofence
- **WHEN** generating the `.poly` file from `fieldProfile.boundary.polygon`
- **THEN** each vertex SHALL be converted via `gcj02ToWgs84()` before writing

### Requirement: Pure function in logic.mjs
The geofence generation function `formatGeofencePoly()` SHALL be a pure function in `logic.mjs` with no DOM or AMap API dependencies.

#### Scenario: Function purity
- **WHEN** `formatGeofencePoly(fieldProfile)` is called
- **THEN** it SHALL return a string without accessing `document`, `window`, or AMap globals
