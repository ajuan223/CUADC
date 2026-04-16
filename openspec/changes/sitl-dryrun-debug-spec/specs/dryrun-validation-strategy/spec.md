## ADDED Requirements

### Requirement: Dry-run SHALL execute the full mission chain
The dry-run SHALL validate the complete state chain: `init → preflight → takeoff → scan → drop-point-routing → release(dry) → landing → completed`. Each state transition SHALL be verified by log assertion.

#### Scenario: Full chain completes without error
- **WHEN** running the dry-run with SITL, mock vision, and `--dry-run` flag
- **THEN** the striker log shows transitions in order: "FSM transition to=preflight", "to=takeoff", "to=scan", "to=enroute" (or drop routing state), "to=release", "to=landing", "to=completed"

### Requirement: Phase 1 - INIT to PREFLIGHT validation
The system SHALL verify that after striker connects to SITL, the first HEARTBEAT triggers `INIT_COMPLETE` and the FSM transitions to `preflight`. During preflight, `upload_full_mission()` SHALL succeed and `landing_sequence_start_index` SHALL be set.

#### Scenario: INIT triggers on first heartbeat
- **WHEN** SITL sends the first HEARTBEAT after connection
- **THEN** striker log shows "FSM transition to=preflight"

#### Scenario: PREFLIGHT uploads mission successfully
- **WHEN** PreflightState executes with SITL
- **THEN** the log shows "Mission upload complete" with the waypoint count, and `landing_sequence_start_index` is set to a positive integer

### Requirement: Phase 2 - TAKEOFF validation
The system SHALL verify that TakeoffState sends ARM and takeoff commands, SITL responds with COMMAND_ACK (ACCEPTED), and the vehicle climbs. The transition to SCAN SHALL occur when altitude reaches 90% of target (72m for 80m target).

#### Scenario: ARM command accepted by SITL
- **WHEN** striker sends MAV_CMD_COMPONENT_ARM_DISARM with force bypass
- **THEN** SITL responds with COMMAND_ACK result=ACCEPTED

#### Scenario: Takeoff mode switch accepted
- **WHEN** striker sends MAV_CMD_DO_SET_MODE with AUTO mode
- **THEN** SITL switches to AUTO mode and begins executing the mission takeoff item

#### Scenario: Altitude threshold triggers SCAN transition
- **WHEN** GLOBAL_POSITION_INT shows relative_alt_m >= 72.0 (90% of 80m)
- **THEN** striker log shows "Target altitude reached" and "FSM transition to=scan"

### Requirement: Phase 3 - SCAN completion validation
The system SHALL verify that ScanState either uses real `MISSION_ITEM_REACHED` messages or the waypoint countdown mechanism to determine scan completion. In SITL with AUTO mode, the vehicle SHALL fly through all 8 scan waypoints.

#### Scenario: Scan waypoints execute in SITL
- **WHEN** SITL is in AUTO mode with the uploaded mission
- **THEN** GLOBAL_POSITION_INT shows the vehicle moving through the scan waypoint pattern

#### Scenario: Scan completion detected
- **WHEN** all scan waypoints are reached (either by MISSION_ITEM_REACHED or countdown)
- **THEN** striker log shows "Scan complete" and transitions to the drop-point routing state

### Requirement: Phase 4 - Drop point routing validation
The system SHALL verify two paths: (a) with mock vision drop point → direct GUIDED goto, (b) without vision drop point → fallback midpoint calculation.

#### Scenario: Vision drop point triggers GUIDED goto
- **WHEN** mock vision server sends a drop point before scan completes
- **THEN** striker sets GUIDED mode and sends SET_POSITION_TARGET to the drop point coordinates

#### Scenario: No drop point triggers fallback midpoint
- **WHEN** no vision drop point is received and scan completes
- **THEN** striker calculates the midpoint between scan end point and landing approach waypoint, then sets GUIDED mode to fly to that midpoint

### Requirement: Phase 5 - RELEASE validation (dry-run)
The system SHALL verify that ReleaseState triggers the release mechanism. In `--dry-run` mode, the actual servo command MAY be suppressed but the log SHALL confirm "Payload released successfully" (or dry-run equivalent).

#### Scenario: Dry-run release completes
- **WHEN** the vehicle reaches the drop point (or a simulated arrival threshold)
- **THEN** striker log shows release triggered and transitions to "landing"

### Requirement: Phase 6 - LANDING validation
The system SHALL verify that LandingState switches to AUTO mode, jumps to the pre-uploaded landing sequence start index, and the SITL vehicle begins the landing approach.

#### Scenario: Landing sequence triggered
- **WHEN** LandingState executes after release
- **THEN** striker sends MAV_CMD_MISSION_SET_CURRENT with the landing start index and SITL begins executing DO_LAND_START → approach waypoint → NAV_LAND

#### Scenario: Touchdown detected
- **WHEN** GLOBAL_POSITION_INT shows relative_alt_m < 1.0
- **THEN** striker log shows "Landing detected" and transitions to "completed"

### Requirement: Phase 7 - Override detection validation
The system SHALL verify that switching SITL to MANUAL mode (via MAVProxy `mode MANUAL`) during any autonomous state triggers OverrideEvent and the FSM enters the `override` terminal state.

#### Scenario: MANUAL mode switch triggers override
- **WHEN** SITL mode is switched to MANUAL during SCAN or ENROUTE
- **THEN** striker log shows "Mode switched to MANUAL" and "FSM transition to=override"

#### Scenario: GUIDED mode does not trigger override
- **WHEN** SITL mode is switched to GUIDED during SCAN
- **THEN** override is NOT triggered (GUIDED is not in the override mode set)

### Requirement: Dry-run SHALL have timeout protection
Each phase SHALL have a maximum duration. If exceeded, the dry-run SHALL report which phase timed out and suggest debug steps from the SITL debug guide.

#### Scenario: Phase timeout detected
- **WHEN** any phase exceeds its configured maximum duration (TAKEOFF: 60s, SCAN: 120s, ENROUTE: 60s, RELEASE: 10s, LANDING: 60s)
- **THEN** the dry-run reports "Phase <name> timed out after <N>s" with debug guidance
