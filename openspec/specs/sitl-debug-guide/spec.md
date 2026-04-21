### Requirement: Debug guide SHALL organize faults by layer
The debug guide SHALL organize all SITL/MAVProxy fault patterns into four layers: Physical/Process Layer, Transport Layer, MAVLink Protocol Layer, and Business Logic Layer. Each fault pattern SHALL define symptoms, root causes, diagnostic commands, and repair actions.

#### Scenario: Fault lookup by symptom
- **WHEN** Claude Code encounters a SITL or MAVLink error during dry-run
- **THEN** it SHALL consult the debug guide, match the symptom to a fault pattern, and follow the prescribed diagnostic steps

### Requirement: Debug guide SHALL document correct SITL port topology
The debug guide SHALL clearly document the port topology so Claude Code can correctly diagnose connection issues:
- **arduplane SITL** (raw binary) listens on **TCP 5760** (base port + 10 * instance)
- **MAVProxy** connects to SITL via TCP 5760, then creates UDP outputs at **14550** and **14551**
- **Striker** (pymavlink) connects to **UDP 14550** (MAVProxy's output, not SITL directly)
- sim_vehicle.py starts both SITL and MAVProxy automatically

#### Scenario: Claude Code understands the port chain
- **WHEN** diagnosing a connection failure
- **THEN** the guide helps Claude Code distinguish between "SITL not running" (`ps aux | grep arduplane`), "MAVProxy not running" (`ps aux | grep mavproxy`), and "UDP 14550 not reachable" (`ss -ulnp | grep 14550`)

### Requirement: Physical/Process Layer debug patterns
The debug guide SHALL cover:

**P-01: SITL process not started**
- Symptom: Connection refused, MAVLink timeout
- Diagnostic: `ps aux | grep arduplane`, `ps aux | grep mavproxy`
- Repair: Start sim_vehicle.py; check for build errors

**P-02: SITL process crashed**
- Symptom: SITL was running but disappeared
- Diagnostic: `dmesg | tail -20`, check stdout/stderr
- Repair: Rebuild SITL binary; verify parameter file syntax

**P-03: Port conflict**
- Symptom: sim_vehicle.py reports address in use
- Diagnostic: `ss -tlnp | grep 5760`, `ss -ulnp | grep 14550`, `lsof -i :5760`
- Repair: Kill conflicting process; check for stale SITL instances

### Requirement: Transport Layer debug patterns
The debug guide SHALL cover:

**T-01: No heartbeat received**
- Symptom: striker `wait_heartbeat()` timeout; "MAVLink connected" never appears
- Diagnostic:
  1. Check SITL alive: `ps aux | grep arduplane`
  2. Check MAVProxy alive: `ps aux | grep mavproxy`
  3. Check UDP 14550: `ss -ulnp | grep 14550`
  4. Test pymavlink: `python -c "from pymavlink import mavutil; c=mavutil.mavlink_connection('udp:127.0.0.1:14550'); c.wait_heartbeat(timeout=5); print('OK')"`
- Repair: Restart sim_vehicle.py; fix pymavlink URL; check firewall

**T-02: Connection lost mid-mission**
- Symptom: HeartbeatMonitor reports timeout during flight
- Diagnostic: Check SITL/MAVProxy still alive; check system resources
- Repair: Restart SITL; increase heartbeat_timeout_s

**T-03: MAVProxy not creating UDP outputs**
- Symptom: UDP 14550 not reachable but SITL is running
- Diagnostic: `ps aux | grep mavproxy`; run `output` in MAVProxy console
- Repair: Restart sim_vehicle.py; or `output add 127.0.0.1:14550` in MAVProxy console

#### Scenario: Heartbeat timeout diagnosis
- **WHEN** striker reports "Heartbeat timeout" at connection
- **THEN** the guide instructs: (1) `ps aux | grep arduplane` (2) `ps aux | grep mavproxy` (3) `ss -ulnp | grep 14550` (4) test pymavlink connectivity

### Requirement: MAVLink Protocol Layer debug patterns
The debug guide SHALL cover:

**M-01: COMMAND_ACK rejected**
- Symptom: `Command N rejected: result=X` in striker log
- Diagnostic: Check result codes (0=ACCEPTED, 3=UNSUPPORTED, 4=FAILED); for ARM verify force-arm bypass param2=21196; for SET_MODE verify ArduPlane mode ID
- Repair: Use force-arm; verify mode ID matches ArduPlaneMode enum

**M-02: Mission upload timeout**
- Symptom: `Timeout waiting for mission request seq=N`
- Diagnostic: Check connection alive; check SITL mode; check queue congestion
- Repair: Increase `_STEP_TIMEOUT`; re-upload mission

**M-03: MISSION_ITEM_REACHED not received**
- Symptom: ScanMonitorState never detects completion
- Diagnostic: Verify AUTO mode (custom_mode==10); verify mission uploaded (`wp list` in MAVProxy); check GLOBAL_POSITION_INT matches waypoint coords
- Repair: Ensure AUTO mode; re-upload mission

**M-04: GUIDED goto has no effect**
- Symptom: Vehicle doesn't change course after SET_POSITION_TARGET
- Diagnostic: Verify GUIDED mode (custom_mode==15); verify type_mask; check coordinates valid; check target_system/component
- Repair: Force GUIDED mode before goto; validate coordinates

**M-05: Mode switch fails silently**
- Symptom: COMMAND_ACK accepted but HEARTBEAT still shows old mode
- Diagnostic: SITL may take 1-2 heartbeat cycles to reflect; verify mode_id matches ArduPlaneMode enum
- Repair: Wait 2 cycles; verify command encoding

#### Scenario: ARM rejected by SITL
- **WHEN** `Command 400 rejected: result=3` appears
- **THEN** the guide instructs: (1) verify param2=21196 (force bypass) (2) try MAVProxy `arm throttle` to confirm behavior

### Requirement: Business Logic Layer debug patterns
The debug guide SHALL cover:

**B-01: State machine stuck in a state**
- Symptom: FSM stops transitioning
- Diagnostic: Check execute() return value; for TAKEOFF check altitude; for SCAN check waypoint progress; for ENROUTE check haversine distance
- Repair: Add debug logging; verify position data updating; check thresholds

**B-02: Vision data not reaching tracker**
- Symptom: `get_smoothed_target()` always None
- Diagnostic: `ps aux | grep mock_vision`; check global_var updates
- Repair: Start mock server; verify port match

**B-03: Landing sequence not executing**
- Symptom: MISSION_SET_CURRENT sent but vehicle doesn't change course
- Diagnostic: Verify landing_sequence_start_index set; verify AUTO mode; check mission still exists
- Repair: Re-upload full mission; verify landing_start_index

**B-04: Override not detected**
- Symptom: MANUAL switch doesn't trigger OverrideEvent
- Diagnostic: Check SafetyMonitor calls OverrideDetector.check_mode(); check HEARTBEAT mode parsing; verify override_modes set
- Repair: Verify HEARTBEAT → mode parsing chain; ensure callback registered

#### Scenario: FSM stuck in TAKEOFF
- **WHEN** striker remains in TAKEOFF > 60 seconds
- **THEN** the guide instructs: (1) check GLOBAL_POSITION_INT altitude (2) verify ARM succeeded (3) verify AUTO mode active (4) check SITL vehicle climbing

### Requirement: Quick-reference diagnostic commands
The debug guide SHALL include copy-paste diagnostic commands:

1. `ps aux | grep arduplane` — SITL process alive
2. `ps aux | grep mavproxy` — MAVProxy process alive
3. `ss -ulnp | grep 14550` — MAVProxy UDP output
4. `ss -tlnp | grep 5760` — SITL TCP server (raw binary)
5. pymavlink quick test: `python -c "from pymavlink import mavutil; c=mavutil.mavlink_connection('udp:127.0.0.1:14550'); c.wait_heartbeat(timeout=5); print('OK sys=%d comp=%d mode=%s' % (c.target_system, c.target_component, c.flightmode))"`

#### Scenario: Quick health check
- **WHEN** Claude Code needs to verify SITL health before starting striker
- **THEN** it runs the diagnostic commands in order: SITL process → MAVProxy process → UDP port → pymavlink test

### Requirement: Structured debug workflow for Claude Code
Claude Code SHALL follow: Capture → Layer Classify → Pattern Match → Diagnose → Repair → Verify → Document

#### Scenario: Claude Code follows structured debug workflow
- **WHEN** a dry-run phase fails
- **THEN** Claude Code (1) captures the error (2) classifies the layer (3) matches a pattern ID (4) runs diagnostics (5) applies repair (6) retries (7) notes new patterns
