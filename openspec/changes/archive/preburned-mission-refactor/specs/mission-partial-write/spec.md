## ADDED Requirements

### Requirement: Partial write SHALL use MISSION_WRITE_PARTIAL_LIST protocol
The system SHALL implement the MAVLink `MISSION_WRITE_PARTIAL_LIST` protocol to overwrite a contiguous range of mission items without clearing the entire mission.

#### Scenario: Overwrite 5 reserved slots during LOITER
- **WHEN** the aircraft is executing `NAV_LOITER_UNLIM` at seq N+1
- **AND** Striker calls `partial_write_mission(start_seq=N+2, end_seq=N+6, items=[approach, target, servo, exit, spare])`
- **THEN** the system SHALL send `MISSION_WRITE_PARTIAL_LIST(start=N+2, end=N+6)` to the flight controller
- **AND** respond to `MISSION_REQUEST_INT` for each seq in [N+2, N+6]
- **AND** verify final `MISSION_ACK(type=ACCEPTED)`

#### Scenario: Partial write does not alter total mission count
- **WHEN** the flight controller has 25 total mission items
- **AND** a partial write overwrites items at seq 15-19
- **THEN** the total mission count SHALL remain 25

#### Scenario: Partial write timeout handling
- **WHEN** any protocol step (request or ack) exceeds 5 seconds
- **THEN** the system SHALL raise `MissionUploadError` with a descriptive message

### Requirement: Partial write SHALL preserve autonomy guard
The system SHALL check `ensure_autonomy_allowed()` before initiating a partial write, consistent with existing mission upload safeguards.

#### Scenario: Partial write blocked after override
- **WHEN** the operator has taken manual control (autonomy relinquished)
- **AND** Striker attempts a partial write
- **THEN** the system SHALL raise `FlightError` without sending any MAVLink messages
