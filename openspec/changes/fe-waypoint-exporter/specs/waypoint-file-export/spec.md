## ADDED Requirements

### Requirement: Generate QGC WPL 110 waypoint file
The system SHALL generate a complete ArduPilot-compatible waypoint file in QGC WPL 110 format from the current field profile and validation state.

The generated file SHALL contain the following mission sequence:
1. HOME waypoint (seq 0): `MAV_CMD_NAV_WAYPOINT` (16), frame=0 (GLOBAL), at touchdown_point with alt=0
2. TAKEOFF (seq 1): `MAV_CMD_NAV_TAKEOFF` (22), frame=3, pitch=15°, alt=scan_altitude_m
3. Scan waypoints (seq 2..N): `MAV_CMD_NAV_WAYPOINT` (16), frame=3, each boustrophedon scan point at scan_altitude_m
4. LOITER_UNLIM (seq N+1): `MAV_CMD_NAV_LOITER_UNLIM` (17), frame=3, at loiter point position
5. DO_LAND_START (seq N+2): `MAV_CMD_DO_LAND_START` (189), frame=3
6. Approach waypoint (seq N+3): `MAV_CMD_NAV_WAYPOINT` (16), frame=3, at derived approach point with approach_alt_m
7. LAND (seq N+4): `MAV_CMD_NAV_LAND` (21), frame=3, at touchdown_point with alt=0

#### Scenario: Successful waypoint export
- **WHEN** user clicks "导出航点" and validation has no blocking errors
- **THEN** system SHALL generate and download a `.waypoints` file with the complete mission sequence

#### Scenario: Blocking errors prevent export
- **WHEN** validation has blocking errors
- **THEN** the waypoint export button SHALL be disabled and no file is generated

### Requirement: All waypoint coordinates in WGS84
Every latitude and longitude written to the `.waypoints` file SHALL be converted from GCJ-02 to WGS84 via `gcj02ToWgs84()`. This includes HOME, scan waypoints, loiter point, approach point, and landing point.

#### Scenario: Coordinate conversion for scan waypoints
- **WHEN** generating scan waypoints from `scanPreview`
- **THEN** each point SHALL be converted via `gcj02ToWgs84()` before writing to file

#### Scenario: Coordinate conversion for landing sequence
- **WHEN** generating approach and landing waypoints
- **THEN** `derivedApproach` and `touchdown_point` coordinates SHALL be converted via `gcj02ToWgs84()`

### Requirement: QGC WPL 110 format compliance
Each line in the output file SHALL be tab-separated with 12 columns: `seq`, `current`, `frame`, `command`, `p1`, `p2`, `p3`, `p4`, `lat`, `lon`, `alt`, `autocontinue`. The first line SHALL be the header `QGC WPL 110`.

#### Scenario: File format validation
- **WHEN** the generated file is loaded into Mission Planner or QGroundControl
- **THEN** the file SHALL parse without errors and display the correct mission sequence on the map

### Requirement: Pure function in logic.mjs
The waypoint generation function `generateWaypointFile()` SHALL be a pure function in `logic.mjs` with no DOM or AMap API dependencies. It SHALL accept `fieldProfile` and `validation` as arguments and return a string.

#### Scenario: Function purity
- **WHEN** `generateWaypointFile(fieldProfile, validation)` is called
- **THEN** it SHALL return a string without accessing `document`, `window`, or AMap globals
