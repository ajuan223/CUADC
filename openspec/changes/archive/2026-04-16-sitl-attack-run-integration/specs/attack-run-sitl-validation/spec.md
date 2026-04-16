## ADDED Requirements

### Requirement: Attack run SITL full-chain validation
The system SHALL complete the full attack run mission chain in SITL: `init → preflight → takeoff → scan → enroute(attack run) → release → landing → completed`. Each state transition SHALL be verified by log assertion with attack-run-specific observables.

#### Scenario: Full attack run chain completes in dry-run mode
- **WHEN** running striker with SITL, mock vision server, and `--dry-run --field sitl_default`
- **THEN** the log shows transitions in order: "FSM transition to=preflight", "to=takeoff", "to=scan", "to=enroute", "to=release", "to=landing", "to=completed"

#### Scenario: Full attack run chain completes in non-dry-run mode
- **WHEN** running striker with SITL and `--field sitl_default` (no dry-run flag)
- **THEN** the log shows the same state transition chain, and DO_SET_SERVO is executed by ArduPlane at target waypoint completion

---

### Requirement: Enroute attack run initiation validation
The system SHALL verify that enroute on_enter uploads the attack+landing mission, switches to AUTO mode, and sets mission current to the approach waypoint sequence.

#### Scenario: Attack mission upload succeeds
- **WHEN** enroute on_enter is called with a valid drop point from mock vision
- **THEN** the striker log shows "attack run mission uploaded" with waypoint count, and `landing_sequence_start_index` is set to the correct seq number (seq of DO_LAND_START)

#### Scenario: AUTO mode switch succeeds
- **WHEN** enroute switches to AUTO mode after mission upload
- **THEN** SITL HEARTBEAT shows custom_mode=10 (ArduPlane AUTO) within 2 heartbeat cycles

#### Scenario: MISSION_SET_CURRENT triggers approach waypoint
- **WHEN** enroute sends MISSION_SET_CURRENT with approach seq
- **THEN** MISSION_CURRENT shows seq=approach_seq and SITL begins navigating toward the approach point

---

### Requirement: Attack run geometry validation in SITL
The system SHALL verify that the attack run geometry (approach/target/exit coordinates) is correctly computed and the waypoints are ordered in the mission.

#### Scenario: Approach heading computed correctly (no wind fallback)
- **WHEN** SITL has no wind simulation and current position is available after scan
- **THEN** approach heading SHALL be the bearing from current position to the drop target, and approach point SHALL be `approach_distance_m` meters behind the target along that bearing

#### Scenario: Approach heading computed with wind data
- **WHEN** SITL is configured with SIM_WIND_DIR and SIM_WIND_SPD > 2 m/s
- **THEN** approach heading SHALL be into the wind (wind_direction + 180 degrees), and approach point SHALL be upwind of the target

#### Scenario: All attack waypoints inside field boundary
- **WHEN** mock vision sends a drop point near field center (30.2650, 120.0950)
- **THEN** approach and exit waypoints (200m offset) SHALL be within the geofence boundary polygon (lat 30.2600-30.2700, lon 120.0900-120.1000)

---

### Requirement: Mission sequence progression validation
The system SHALL verify that mission_current_seq advances correctly through the attack run waypoints: approach → target → exit.

#### Scenario: Mission seq advances from approach to target
- **WHEN** SITL reaches the approach waypoint in AUTO mode
- **THEN** mission_current_seq advances to target seq, and striker logs the progression

#### Scenario: Target waypoint completion triggers release transition
- **WHEN** mission_current_seq >= target_seq + 1
- **THEN** enroute SHALL return Transition(target_state="release")

#### Scenario: Mission seq advances through exit to landing
- **WHEN** release state completes and landing state executes
- **THEN** mission_current_seq advances to landing start index and SITL begins landing approach

---

### Requirement: DO_SET_SERVO execution timing validation
In non-dry-run mode, the system SHALL verify that DO_SET_SERVO executes when the target waypoint is completed (between target and exit waypoint execution).

#### Scenario: DO_SET_SERVO triggered at target completion
- **WHEN** running in non-dry-run mode and SITL completes the target waypoint
- **THEN** SERVO_OUTPUT_RAW shows the release servo channel changed to the configured PWM value, and striker log shows "Payload released (native DO_SET_SERVO)"

#### Scenario: DO_SET_SERVO not present in dry-run mission
- **WHEN** running in dry-run mode
- **THEN** the uploaded mission SHALL NOT contain DO_SET_SERVO items, and release is handled by companion computer

---

### Requirement: Release precision measurement
The system SHALL record the actual distance between the vehicle position at target waypoint completion and the intended drop point coordinates.

#### Scenario: Precision recorded in dry-run log
- **WHEN** the target waypoint is reached in SITL
- **THEN** the striker log SHALL include the haversine distance between GLOBAL_POSITION_INT at that moment and the target coordinates, labeled as "release_distance_m"

#### Scenario: Precision within WP_RADIUS
- **WHEN** ArduPlane uses default WP_RADIUS (~30m)
- **THEN** the recorded release_distance_m SHALL be <= 30m

---

### Requirement: Landing after attack run validation
The system SHALL verify that landing state correctly jumps to the pre-uploaded landing sequence without re-uploading a mission.

#### Scenario: Landing uses pre-uploaded landing sequence
- **WHEN** entering LANDING state after attack run
- **THEN** striker sends MISSION_SET_CURRENT with the landing start index (recorded during enroute on_enter), and SITL begins DO_LAND_START → approach waypoint → NAV_LAND

#### Scenario: No mission re-upload during landing
- **WHEN** landing state executes after attack run
- **THEN** no MISSION_CLEAR_ALL or MISSION_COUNT messages SHALL be sent; only MISSION_SET_CURRENT

#### Scenario: Touchdown detected after landing approach
- **WHEN** SITL completes the landing sequence
- **THEN** GLOBAL_POSITION_INT shows relative_alt_m < 1.0, striker log shows "Landing detected", and FSM transitions to "completed"

---

### Requirement: Attack run fallback path validation (no vision)
The system SHALL verify the attack run works when no vision drop point is received, using the fallback midpoint calculation.

#### Scenario: Fallback midpoint attack run
- **WHEN** mock vision server runs with `--no-drop-point` and scan completes
- **THEN** striker calculates the fallback midpoint, uploads attack run mission targeting that midpoint, and the chain continues to release → landing → completed

---

### Requirement: Attack run phase timeout protection
Each attack run phase SHALL have a maximum duration with specific timeouts reflecting the attack run flight characteristics.

#### Scenario: Enroute attack run timeout
- **WHEN** enroute state exceeds 90 seconds (accounting for approach + target + exit flight time at ~20m/s over 400m + margin)
- **THEN** the dry-run reports "Phase enroute timed out after 90s" with attack-run-specific debug guidance

#### Scenario: Phase timeouts for attack run chain
- **WHEN** the following maximum durations are configured: TAKEOFF=60s, SCAN=120s, ENROUTE=90s, RELEASE=10s, LANDING=60s
- **THEN** any phase exceeding its timeout SHALL be reported with the corresponding fault pattern reference

---

### Requirement: Attack run log assertion patterns
The system SHALL define specific log patterns for each attack run phase to enable automated dry-run verification.

#### Scenario: Enroute phase log patterns
- **WHEN** enroute state executes the attack run
- **THEN** the following log patterns SHALL appear in order:
  1. "attack run mission uploaded" (on_enter)
  2. "approach heading" with computed bearing (on_enter)
  3. "MISSION_SET_CURRENT" with approach seq (on_enter)
  4. Periodic "mission_current_seq" updates (execute)
  5. "mission_current_seq >= target_seq" triggering transition (execute)

#### Scenario: Release phase log patterns (dry-run)
- **WHEN** entering release state in dry-run mode
- **THEN** the log SHALL show "Payload released (dry-run)" or equivalent dry-run release log

#### Scenario: Landing phase log patterns
- **WHEN** entering landing state after attack run
- **THEN** the log SHALL show "mission_set_current to landing_start_index" and "landing approach executing"

---

### Requirement: Attack run debug fault patterns
The SITL debug guide SHALL be extended with attack-run-specific fault patterns for structured troubleshooting.

#### Scenario: M-06 MISSION_SET_CURRENT has no effect
- **WHEN** MISSION_SET_CURRENT is sent but mission_current_seq does not change
- **THEN** the debug guide instructs: (1) verify AUTO mode active (2) verify mission uploaded and not empty (3) verify seq number within mission range (4) check COMMAND_ACK response

#### Scenario: M-07 mission_current_seq does not advance
- **WHEN** SITL is in AUTO mode with valid mission but seq stays at approach
- **THEN** the debug guide instructs: (1) check GLOBAL_POSITION_INT approaching approach point (2) verify WP_RADIUS reasonable (3) check wind speed not preventing progress (4) verify mission items have correct coordinates

#### Scenario: M-08 DO_SET_SERVO not triggered
- **WHEN** running in non-dry-run mode and target waypoint completes but servo does not activate
- **THEN** the debug guide instructs: (1) verify DO_SET_SERVO is in mission at correct seq (2) check SERVO_OUTPUT_RAW for PWM change (3) verify servo channel and PWM match release config (4) check SITL parameter SERVOx_FUNCTION

#### Scenario: B-05 Attack run approach/exit points outside boundary
- **WHEN** approach or exit coordinates fall outside the geofence boundary
- **THEN** the debug guide instructs: (1) verify drop point is sufficiently inside boundary (2) check approach_distance_m and exit_distance_m configuration (3) consider reducing distances or centering drop point
