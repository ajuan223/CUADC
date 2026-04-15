## ADDED Requirements

### Requirement: Business states use haversine_distance for GPS distance
All business states (EnrouteState, ApproachState, ForcedStrikeState) SHALL use `striker.utils.geo.haversine_distance()` for GPS distance calculations instead of hardcoded degree-to-meter approximations.

#### Scenario: EnrouteState uses haversine for approach distance check
- **WHEN** `EnrouteState.execute()` calculates distance to target
- **THEN** it calls `haversine_distance(pos.lat, pos.lon, tgt.lat, tgt.lon)` from `striker.utils.geo`

#### Scenario: ApproachState uses haversine for release point arrival check
- **WHEN** `ApproachState.execute()` calculates distance to release point
- **THEN** it calls `haversine_distance()` from `striker.utils.geo`

#### Scenario: No hardcoded 111000 coefficients in state files
- **WHEN** a grep for `111.?000` is run on `src/striker/core/states/`
- **THEN** zero matches are found

### Requirement: forced_strike_point validates safety buffer via boundary distance
`generate_forced_strike_point()` SHALL reject candidate points whose distance to the nearest polygon edge is less than `buffer_m`. The point-to-segment distance function SHALL be a shared utility in `striker.utils.geo`.

#### Scenario: Generated point is at least buffer_m from boundary
- **WHEN** `generate_forced_strike_point(polygon, buffer_m=50)` returns a point
- **THEN** the point's distance to the nearest polygon edge is >= 50 meters

#### Scenario: Point too close to boundary is rejected
- **WHEN** a candidate random point has boundary distance < buffer_m
- **THEN** the point is rejected and the algorithm tries another candidate

#### Scenario: point_to_segment_distance is in utils.geo
- **WHEN** `from striker.utils.geo import point_to_segment_distance` is executed
- **THEN** the import succeeds and returns a callable

### Requirement: LandingState uses pre-uploaded landing sequence
`LandingState` SHALL trigger the pre-uploaded landing sequence (uploaded during PREFLIGHT via DO_LAND_START + approach waypoint + NAV_LAND) by setting AUTO mode and sending `MAV_CMD_MISSION_SET_CURRENT` to jump to the landing sequence start index. It SHALL NOT use RTL mode as the landing method.

#### Scenario: LandingState triggers landing sequence
- **WHEN** `LandingState.execute()` runs for the first time
- **THEN** it sends a `MAV_CMD_MISSION_SET_CURRENT` command pointing to the landing sequence start index and sets AUTO mode

#### Scenario: LandingState does not use RTL
- **WHEN** `LandingState.execute()` is inspected
- **THEN** it does NOT reference `ArduPlaneMode.RTL` for triggering the landing

### Requirement: ApproachState passes velocity and wind to ballistic calculator
`ApproachState` SHALL extract current airspeed/groundspeed and wind data from the mission context (via telemetry) and pass them as `velocity_n_mps`, `velocity_e_mps`, `wind_n_mps`, `wind_e_mps` to `ballistic_calculator.calculate_release_point()`.

#### Scenario: Ballistic calculator receives non-zero velocity when available
- **WHEN** the aircraft is flying at 20 m/s groundspeed heading north
- **THEN** `calculate_release_point()` is called with `velocity_n_mps > 0` (not default 0)

#### Scenario: Ballistic calculator receives wind data when available
- **WHEN** wind data is available in telemetry
- **THEN** `calculate_release_point()` is called with `wind_n_mps` and `wind_e_mps` populated
