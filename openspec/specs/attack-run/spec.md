### Requirement: Attack run geometry calculation
The system SHALL compute attack run geometry given a target drop point: an approach point offset from the target along the upwind bearing (or direct bearing from current position if no wind data), and an exit point offset beyond the target along the same heading. Approach and exit distances SHALL be configurable via field profile.

#### Scenario: Upwind approach with wind data
- **WHEN** wind data is available with speed > 2 m/s and direction 0° (north wind)
- **THEN** approach heading SHALL be 0° (into the wind), approach point SHALL be 200m south of target, exit point SHALL be 200m north of target

#### Scenario: Fallback to direct bearing without wind
- **WHEN** no wind data is available and current position is south of the target
- **THEN** approach heading SHALL be the bearing from current position to target

#### Scenario: Ultimate fallback using landing heading
- **WHEN** no wind data and no current position are available
- **THEN** approach heading SHALL be the reverse of field profile's `landing.heading_deg`

---

### Requirement: Attack run mission generation
The system SHALL generate a MAVLink mission sequence for the attack run containing: dummy HOME (seq 0), approach waypoint (seq 1), target waypoint (seq 2), DO_SET_SERVO (seq 3, only when not dry_run), exit waypoint (seq 4 or seq 3 when dry_run), followed by landing sequence items. The landing start index SHALL be recorded in context.

#### Scenario: Mission generation in non-dry-run mode
- **WHEN** `build_attack_run_mission()` is called with `dry_run=False`
- **THEN** the mission SHALL contain DO_SET_SERVO at the sequence after target waypoint, with channel and PWM from release config, followed by exit waypoint and landing items

#### Scenario: Mission generation in dry-run mode
- **WHEN** `build_attack_run_mission()` is called with `dry_run=True`
- **THEN** the mission SHALL NOT contain DO_SET_SERVO; exit waypoint SHALL immediately follow target waypoint

#### Scenario: NAV_WAYPOINT parameters for target
- **WHEN** target waypoint is created
- **THEN** `param2` (acceptance radius) SHALL be set from field profile `attack_run.release_acceptance_radius_m` if configured, otherwise 0 (use ArduPlane default WP_RADIUS)

---

### Requirement: Enroute state executes attack run
The ENROUTE state SHALL upload the attack+landing mission, switch to AUTO mode, set mission current to the approach waypoint sequence, and monitor `mission_current_seq` for completion of the target waypoint.

#### Scenario: Successful attack run initiation
- **WHEN** enroute on_enter is called with a valid drop point
- **THEN** the system SHALL upload the attack+landing mission, switch to AUTO mode, set current waypoint to approach, and set `_attack_active = True`

#### Scenario: Target waypoint completed triggers transition
- **WHEN** `_attack_active` is True and `mission_current_seq >= target_seq + 1`
- **THEN** enroute SHALL return `Transition(target_state="release")`

#### Scenario: No drop point set
- **WHEN** enroute on_enter is called with `context.active_drop_point == None`
- **THEN** the system SHALL log an error and not initiate the attack run

---

### Requirement: Release state confirms native release
When `dry_run=False`, the RELEASE state SHALL verify that the native DO_SET_SERVO has executed (by checking mission progress or elapsed time) and log the release event. When `dry_run=True`, RELEASE state SHALL call `context.release_controller.release()` which logs without physical servo activation.

#### Scenario: Non-dry-run release confirmation
- **WHEN** entering RELEASE state with `dry_run=False`
- **THEN** the system SHALL log "Payload released (native DO_SET_SERVO)" and immediately transition to LANDING

#### Scenario: Dry-run release via companion
- **WHEN** entering RELEASE state with `dry_run=True`
- **THEN** the system SHALL call `context.release_controller.release()` and transition to LANDING on success

---

### Requirement: Landing state uses pre-uploaded mission
The LANDING state SHALL set mission current to the landing start index in the attack+landing mission. No mission re-upload SHALL be needed.

#### Scenario: Landing trigger after attack run
- **WHEN** entering LANDING state after attack run
- **THEN** the system SHALL set `mission_set_current` to the DO_LAND_START sequence index and monitor altitude for touchdown
