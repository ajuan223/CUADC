## MODIFIED Requirements

### Requirement: PreflightState shall upload geofence to FC
PreflightState is **removed**. Replaced by StandbyState which downloads and validates the preburned mission from the flight controller instead of uploading.

**Reason**: Mission is preburned via Mission Planner; Striker no longer generates or uploads missions.
**Migration**: PreflightState logic replaced by StandbyState (mission download + validation).

### Requirement: PreflightState shall upload landing sequence to FC
PreflightState is **removed**. Landing sequence is part of the preburned mission.

**Reason**: Landing sequence is preburned in flight controller.
**Migration**: Removed; landing seq index parsed from downloaded mission in StandbyState.

### Requirement: TakeoffState shall send ARM + takeoff commands
TakeoffState is **removed**. Aircraft is armed and takes off under human/Mission Planner control.

**Reason**: Striker no longer manages takeoff; flight controller executes preburned takeoff sequence autonomously or under pilot control.
**Migration**: Removed entirely.

### Requirement: TakeoffState shall wait for target altitude before transitioning
TakeoffState is **removed**.

**Reason**: See above.
**Migration**: Removed entirely.

## REMOVED Requirements

### Requirement: REQ-PREFLIGHT-001 through REQ-PREFLIGHT-003
**Reason**: Preflight upload replaced by mission download/validation in StandbyState.
**Migration**: Use StandbyState which downloads preburned mission and validates structure.

### Requirement: REQ-TAKEOFF-001 and REQ-TAKEOFF-002
**Reason**: Takeoff managed by flight controller / pilot, not Striker.
**Migration**: Removed; Striker starts in STANDBY and monitors scan progress.

### Requirement: REQ-ENROUTE-001 and REQ-ENROUTE-002
**Reason**: Enroute attack run via mission upload replaced by partial write + MISSION_SET_CURRENT in LOITER_HOLD and ATTACK_RUN states.
**Migration**: Use loiter-hold-inject for drop point injection; ATTACK_RUN monitors approach progress.

## ADDED Requirements

### Requirement: State machine SHALL follow preburned mission flow
The state machine SHALL transition through: INIT → STANDBY → SCAN_MONITOR → LOITER_HOLD → ATTACK_RUN → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED.

#### Scenario: Normal mission flow
- **WHEN** Striker starts and connects to flight controller
- **THEN** the FSM SHALL progress through INIT → STANDBY → SCAN_MONITOR → LOITER_HOLD → ATTACK_RUN → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED

#### Scenario: Override and emergency interceptors preserved
- **WHEN** an OverrideEvent or EmergencyEvent occurs in any state
- **THEN** the FSM SHALL transition to OVERRIDE or EMERGENCY respectively

### Requirement: StandbyState SHALL download and validate preburned mission
StandbyState SHALL use the mission-download capability to read the preburned mission, parse critical seq numbers, and validate structure before transitioning to SCAN_MONITOR.

#### Scenario: Successful mission validation
- **WHEN** Striker connects to flight controller and heartbeat is established
- **THEN** StandbyState SHALL download all mission items
- **AND** parse loiter_seq, slot_start_seq, slot_end_seq, landing_start_seq
- **AND** transition to SCAN_MONITOR

#### Scenario: Invalid preburned mission
- **WHEN** the downloaded mission fails validation (missing LOITER, insufficient slots, no landing)
- **THEN** StandbyState SHALL log a critical error and remain in STANDBY

### Requirement: SCAN_MONITOR SHALL passively observe scan progress
SCAN_MONITOR SHALL monitor `mission_current_seq` without uploading or modifying any mission items.

#### Scenario: Detect scan completion
- **WHEN** `mission_current_seq` reaches `loiter_seq`
- **THEN** SCAN_MONITOR SHALL transition to LOITER_HOLD

### Requirement: LANDING_MONITOR SHALL detect touchdown without uploading missions
LANDING_MONITOR SHALL monitor landing progress using STATUSTEXT and altitude telemetry without uploading any landing-only missions.

#### Scenario: Detect landing via status text
- **WHEN** STATUSTEXT contains "hit ground" or "land complete" or "throttle disarmed"
- **AND** relative altitude is below 5m
- **THEN** LANDING_MONITOR SHALL transition to COMPLETED
