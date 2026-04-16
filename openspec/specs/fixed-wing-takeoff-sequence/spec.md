## ADDED Requirements

### Requirement: Fixed-wing takeoff starts from a pre-uploaded AUTO mission
For ArduPlane fixed-wing operation, the system SHALL initiate takeoff from a pre-uploaded mission whose first mission item is `NAV_TAKEOFF`. The takeoff trigger SHALL select mission index `0` and enter `AUTO`; it SHALL NOT send a direct `COMMAND_LONG MAV_CMD_NAV_TAKEOFF` as the primary takeoff path.

#### Scenario: Takeoff starts uploaded mission
- **WHEN** `TakeoffState.execute()` triggers takeoff for a fixed-wing mission
- **THEN** the flight controller MUST set the current mission item to `0`
- **AND** it MUST switch the vehicle to `AUTO`
- **AND** it MUST NOT issue a direct `COMMAND_LONG MAV_CMD_NAV_TAKEOFF` request

### Requirement: PREFLIGHT uploads a full fixed-wing mission
`PreflightState` SHALL upload one complete fixed-wing mission before transitioning to TAKEOFF. The uploaded mission SHALL contain, in order, a `NAV_TAKEOFF` item, all configured scan waypoints, and the landing sequence items.

#### Scenario: Uploaded mission contains takeoff, scan, and landing phases
- **WHEN** `PreflightState.execute()` completes mission preparation
- **THEN** the uploaded mission MUST begin with `NAV_TAKEOFF`
- **AND** the scan waypoints MUST follow in configured order
- **AND** the landing sequence (`DO_LAND_START`, approach waypoint, `NAV_LAND`) MUST remain in the same uploaded mission

### Requirement: Landing uses the uploaded mission landing start index
The mission preparation step SHALL compute the landing sequence start index for the full uploaded mission and make it available to `LandingState`. `LandingState` SHALL jump to that stored landing start index when triggering landing.

#### Scenario: Landing jump accounts for takeoff prefix
- **WHEN** `LandingState.execute()` triggers landing after the full fixed-wing mission was uploaded
- **THEN** it MUST use the stored landing-sequence start index from mission preparation
- **AND** that index MUST point to the first landing-sequence item after the takeoff item and scan waypoints
