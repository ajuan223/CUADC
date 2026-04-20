# mission-upload

## Requirements

- REQ-MISSION-001: Upload shall follow strict MAVLink micro-protocol regardless of whether mission items are hand-authored or procedurally generated
- REQ-MISSION-002: Step 1: MISSION_CLEAR_ALL → verify MISSION_ACK
- REQ-MISSION-003: Step 2: MISSION_COUNT with total item count
- REQ-MISSION-004: Step 3: Respond to MISSION_REQUEST_INT per item by index
- REQ-MISSION-005: Step 4: Final MISSION_ACK verification (type == ACCEPTED)
- REQ-MISSION-006: Timeout handling for each protocol step

### Requirement: Scan waypoints generated from procedural field constraints
The system SHALL upload scan mission items generated from field scan constraints instead of directly consuming a user-authored scan waypoint list from `FieldProfile`.

#### Scenario: Upload generated scan path
- **WHEN** mission preparation completes with a procedurally generated scan path
- **THEN** the upload pipeline SHALL serialize and upload that generated waypoint sequence as MAVLink mission items

### Requirement: Landing sequence generated from procedural landing config
The system SHALL upload a landing sequence whose approach waypoint is procedurally derived from landing configuration facts instead of consuming a user-authored approach coordinate.

#### Scenario: Upload generated landing approach
- **WHEN** mission preparation completes with a procedurally generated landing sequence
- **THEN** the upload pipeline SHALL serialize and upload the derived approach waypoint and `NAV_LAND` item
- **AND** the landing start index stored in context SHALL point to the first procedurally generated landing item
