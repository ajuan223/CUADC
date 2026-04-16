## MODIFIED Requirements

### Requirement: Fixed-wing takeoff starts from a procedurally generated AUTO mission
For ArduPlane fixed-wing operation, the system SHALL initiate takeoff from a pre-uploaded AUTO mission whose first flight segment is generated from field runway facts. The takeoff trigger SHALL select the generated mission start index and enter `AUTO`; it SHALL NOT require users to pre-author fixed-wing takeoff mission points in field configuration.

#### Scenario: Takeoff starts generated mission
- **WHEN** `TakeoffState.execute()` triggers takeoff for a fixed-wing mission
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
