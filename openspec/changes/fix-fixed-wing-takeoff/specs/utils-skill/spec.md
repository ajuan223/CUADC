## MODIFIED Requirements

### Requirement: LandingState uses pre-uploaded landing sequence
`LandingState` SHALL trigger the pre-uploaded landing sequence from the full mission uploaded during PREFLIGHT by setting AUTO mode and sending `MAV_CMD_MISSION_SET_CURRENT` to jump to the stored landing sequence start index. The full mission SHALL preserve the landing sequence items (`DO_LAND_START` + approach waypoint + `NAV_LAND`) after the takeoff item and scan waypoints. It SHALL NOT use RTL mode as the landing method.

#### Scenario: LandingState triggers landing sequence
- **WHEN** `LandingState.execute()` runs for the first time
- **THEN** it sends a `MAV_CMD_MISSION_SET_CURRENT` command pointing to the stored landing sequence start index and sets AUTO mode

#### Scenario: LandingState does not use RTL
- **WHEN** `LandingState.execute()` is inspected
- **THEN** it does NOT reference `ArduPlaneMode.RTL` for triggering the landing
