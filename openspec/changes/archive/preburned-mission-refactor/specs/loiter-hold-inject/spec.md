## ADDED Requirements

### Requirement: LOITER_HOLD state SHALL detect aircraft entering loiter
The system SHALL transition into LOITER_HOLD when `mission_current_seq` equals the preburned `loiter_seq` (NAV_LOITER_UNLIM).

#### Scenario: Detect loiter entry
- **WHEN** `mission_current_seq` equals `loiter_seq` (e.g., seq 12)
- **THEN** the system SHALL enter LOITER_HOLD state
- **AND** log the loiter detection event

### Requirement: LOITER_HOLD state SHALL resolve drop point from vision global variable
The system SHALL read the vision global variable `VISION_DROP_POINT` to obtain the drop point coordinates. If unavailable, it SHALL use the fallback drop point from field_profile configuration.

#### Scenario: Vision drop point available
- **WHEN** `VISION_DROP_POINT` is `(30.261, 120.095)` (not None)
- **THEN** the system SHALL use `(30.261, 120.095)` as the active drop point
- **AND** set `drop_point_source` to `"vision"`

#### Scenario: Vision drop point unavailable — use fallback
- **WHEN** `VISION_DROP_POINT` is None
- **AND** `field_profile.attack_run.fallback_drop_point` is `GeoPoint(lat=30.260, lon=120.094)`
- **THEN** the system SHALL use `(30.260, 120.094)` as the active drop point
- **AND** set `drop_point_source` to `"fallback_field"`

#### Scenario: Both vision and fallback unavailable
- **WHEN** `VISION_DROP_POINT` is None
- **AND** `field_profile.attack_run.fallback_drop_point` is None
- **THEN** the system SHALL log an error and remain in LOITER_HOLD indefinitely

### Requirement: LOITER_HOLD state SHALL overwrite reserved slots via partial write
After resolving the drop point, the system SHALL compute approach/exit waypoints and overwrite the 5 reserved mission slots using `MISSION_WRITE_PARTIAL_LIST`.

#### Scenario: Overwrite slots with attack geometry
- **WHEN** drop point is resolved at `(30.261, 120.095)`
- **THEN** the system SHALL compute approach waypoint (behind target along approach heading)
- **AND** compute exit waypoint (ahead of target toward landing approach)
- **AND** call `partial_write_mission()` to overwrite slots 0-4 with [approach, target, DO_SET_SERVO, exit, spare]

### Requirement: LOITER_HOLD state SHALL unblock mission via MISSION_SET_CURRENT
After successful partial write, the system SHALL send `MISSION_SET_CURRENT(seq=slot_start_seq)` to jump the flight controller past the LOITER_UNLIM and begin flying toward the approach waypoint.

#### Scenario: Unblock after successful write
- **WHEN** partial write completes successfully
- **THEN** the system SHALL send `MISSION_SET_CURRENT(seq=slot_start_seq)`
- **AND** transition to ATTACK_RUN state
- **AND** log the unblock event with the resolved drop point coordinates

#### Scenario: Partial write failure — remain in loiter
- **WHEN** partial write raises `MissionUploadError`
- **THEN** the system SHALL log the error
- **AND** remain in LOITER_HOLD state
- **AND** retry on next execute cycle
