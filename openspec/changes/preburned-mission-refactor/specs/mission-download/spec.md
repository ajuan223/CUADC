## ADDED Requirements

### Requirement: Mission download SHALL read all items from flight controller
The system SHALL implement the MAVLink Mission Download Protocol to retrieve the complete mission stored in the flight controller at startup.

#### Scenario: Download full mission from flight controller
- **WHEN** Striker enters STANDBY state with an active MAVLink connection
- **THEN** the system SHALL send `MISSION_REQUEST_LIST` to get the total item count
- **AND** send `MISSION_REQUEST_INT` for each seq from 0 to count-1
- **AND** store all received `MISSION_ITEM_INT` messages in an ordered list

#### Scenario: Download timeout handling
- **WHEN** any download step exceeds 5 seconds
- **THEN** the system SHALL raise `MissionDownloadError` with a descriptive message

### Requirement: Mission download SHALL parse critical sequence numbers
The system SHALL scan downloaded mission items to identify and store the following key indices: `loiter_seq`, `slot_start_seq`, `slot_end_seq`, `landing_start_seq`.

#### Scenario: Identify LOITER_UNLIM as the hold point
- **WHEN** downloaded mission contains a `NAV_LOITER_UNLIM` (cmd=17) item at seq 12
- **THEN** `loiter_seq` SHALL be set to 12
- **AND** `slot_start_seq` SHALL be set to 13
- **AND** `slot_end_seq` SHALL be set to 17 (5 slots: 13,14,15,16,17)

#### Scenario: Identify landing sequence start
- **WHEN** downloaded mission contains a `DO_LAND_START` (cmd=189) item at seq 18
- **THEN** `landing_start_seq` SHALL be set to 18

#### Scenario: Identify landing without DO_LAND_START
- **WHEN** downloaded mission has no `DO_LAND_START` but has `NAV_LAND` (cmd=21) at seq 19
- **THEN** `landing_start_seq` SHALL be set to 19

### Requirement: Mission download SHALL validate preburned mission structure
The system SHALL reject missions that do not conform to the expected preburned structure.

#### Scenario: Reject mission without LOITER_UNLIM
- **WHEN** downloaded mission contains no `NAV_LOITER_UNLIM` item
- **THEN** the system SHALL raise `ConfigError` with message indicating missing loiter hold point

#### Scenario: Reject mission with insufficient reserved slots
- **WHEN** the number of items between `loiter_seq` and `landing_start_seq` is less than 5
- **THEN** the system SHALL raise `ConfigError` with message indicating insufficient reserved slots

#### Scenario: Reject mission without landing sequence
- **WHEN** downloaded mission contains neither `DO_LAND_START` nor `NAV_LAND`
- **THEN** the system SHALL raise `ConfigError` with message indicating missing landing sequence
