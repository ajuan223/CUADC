**Status: Obsolete/Replaced**
**Reason**: Replaced by `preburned-mission-refactor`. The concepts in this specification (such as procedural mission generation or the old state chain `PREFLIGHT → ENROUTE`) are no longer used in the current `GUIDED` takeover architecture.

## REMOVED Requirements

**Reason**: Replaced by `preburned-mission-refactor`. Takeoff is now part of the preburned mission uploaded externally; Striker no longer generates takeoff geometry at runtime.

**Migration**: See `guided-strike-control-loop` spec.

---

## Requirements (OBSOLETE — kept for historical reference)
For ArduPlane fixed-wing operation, the system SHALL initiate takeoff from a pre-uploaded AUTO mission whose first flight segment is generated from field runway facts. The takeoff trigger SHALL select the generated mission start index and enter `AUTO`; it SHALL NOT require users to pre-author fixed-wing takeoff mission points in field configuration.

#### Scenario: Takeoff starts generated mission
- **WHEN** the system begins the takeoff phase for a fixed-wing mission
- **THEN** the flight controller MUST set the current mission item to the generated takeoff start index
- **AND** it MUST switch the vehicle to `AUTO`
- **AND** the uploaded takeoff segment MUST have been procedurally generated from runway/location facts
- **AND** it MUST NOT depend on hand-authored takeoff mission points in field configuration

### Requirement: PREFLIGHT uploads a full fixed-wing mission
`PreflightState` SHALL upload one complete fixed-wing mission before transitioning to TAKEOFF. The uploaded mission SHALL contain, in order, a generated takeoff segment, procedurally generated scan waypoints, and the landing sequence items.

#### Scenario: Uploaded mission contains generated takeoff, scan, and landing phases
- **WHEN** `PreflightState.execute()` completes mission preparation
- **THEN** the uploaded mission MUST begin with the procedurally generated takeoff segment
- **AND** the generated scan waypoints MUST follow in generated order
- **AND** the generated landing sequence MUST remain in the same uploaded mission
