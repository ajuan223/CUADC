## MODIFIED Requirements

### Requirement: Upload shall follow strict MAVLink micro-protocol
Upload SHALL follow the strict MAVLink mission micro-protocol regardless of whether mission items are hand-authored or procedurally generated.

#### Scenario: Procedurally generated mission uploads via standard protocol
- **WHEN** mission preparation produces a procedurally generated mission
- **THEN** upload SHALL still perform `MISSION_CLEAR_ALL`, `MISSION_COUNT`, `MISSION_REQUEST_INT` handling, and final `MISSION_ACK` verification in order

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
