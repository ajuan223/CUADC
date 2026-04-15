## Phase 3: MAVLink Communication Layer

### 3.1 Package Scaffold

- [x] 3.1.0 Use Context7 MCP to query `pymavlink` and `geopy` documentation for best practices
- [x] 3.1.1 Create `src/striker/comms/__init__.py` with module docstring
- [x] 3.1.2 Add `geopy` to project dependencies in pyproject.toml
- [x] 3.1.3 Add `python-statemachine` to project dependencies in pyproject.toml
- [x] 3.1.4 Verify all new dependencies resolve with `uv sync`

### 3.2 Connection — Data Types

- [x] 3.2.1 Define `ConnectionState` enum in `comms/connection.py` (DISCONNECTED, CONNECTING, CONNECTED, LOST)
- [x] 3.2.2 Define transport URL parsing helper (serial vs UDP detection)

### 3.3 Connection — MAVLinkConnection Class

- [x] 3.3.1 Implement `MAVLinkConnection.__init__()` with settings, queue, event, state
- [x] 3.3.2 Implement `async connect()` — call mavlink_connection, wait first heartbeat
- [x] 3.3.3 Implement `_rx_loop()` — recv_match(blocking=False) + asyncio.Queue push + 5ms sleep yield
- [x] 3.3.4 Implement `async run()` — start rx_loop as task
- [x] 3.3.5 Implement `send(msg)` — thread-safe message send via mav master
- [x] 3.3.6 Implement `async recv_match(type, timeout)` — consumer with asyncio.wait_for on queue
- [x] 3.3.7 Implement `disconnect()` — cleanup and state reset
- [x] 3.3.8 Add connection state change callback registration

### 3.4 Heartbeat Monitor

- [x] 3.4.1 Create `src/striker/comms/heartbeat.py`
- [x] 3.4.2 Implement `HeartbeatMonitor.__init__()` with timeout config and asyncio.Event
- [x] 3.4.3 Implement periodic heartbeat send coroutine (1Hz, configurable)
- [x] 3.4.4 Implement heartbeat receive watchdog with asyncio.wait_for
- [x] 3.4.5 Implement `is_healthy` property
- [x] 3.4.6 Add health status change callback support

### 3.5 Message Helpers

- [x] 3.5.1 Create `src/striker/comms/messages.py`
- [x] 3.5.2 Define message type constants (HEARTBEAT, GLOBAL_POSITION_INT, VFR_HUD, etc.)
- [x] 3.5.3 Implement `send_command_long()` wrapper with timeout parameter
- [x] 3.5.4 Implement `async wait_for_message(type, timeout)` helper
- [x] 3.5.5 Implement `async wait_for_command_ack(command_id, timeout)` helper

### 3.6 Telemetry Parser

- [x] 3.6.1 Create `src/striker/comms/telemetry.py`
- [x] 3.6.2 Define `GeoPosition` dataclass (lat, lon, alt_m, relative_alt_m)
- [x] 3.6.3 Define `AttitudeData` dataclass (roll_rad, pitch_rad, yaw_rad)
- [x] 3.6.4 Define `SpeedData` dataclass (airspeed_mps, groundspeed_mps)
- [x] 3.6.5 Define `WindData` dataclass (direction_deg, speed_mps)
- [x] 3.6.6 Define `BatteryData` dataclass (voltage_v, current_a, remaining_pct)
- [x] 3.6.7 Define `SystemStatus` dataclass (mode, armed, system_status)
- [x] 3.6.8 Implement `TelemetryParser` class with parse method dispatch table
- [x] 3.6.9 Implement GLOBAL_POSITION_INT → GeoPosition conversion (1e7 scale)
- [x] 3.6.10 Implement ATTITUDE → AttitudeData conversion
- [x] 3.6.11 Implement VFR_HUD → SpeedData conversion
- [x] 3.6.12 Implement WIND → WindData conversion
- [x] 3.6.13 Implement SYS_STATUS → BatteryData conversion
- [x] 3.6.14 Implement HEARTBEAT → SystemStatus conversion
- [x] 3.6.15 Wire TelemetryParser into rx_loop message routing

### 3.7 Comms Unit Tests

- [x] 3.7.1 Create `tests/unit/test_connection.py`
- [x] 3.7.2 Test: MAVLinkConnection init with default settings
- [x] 3.7.3 Test: transport URL parsing — serial vs UDP detection
- [x] 3.7.4 Test: connection state transitions (DISCONNECTED→CONNECTING→CONNECTED→LOST)
- [x] 3.7.5 Test: rx_loop pushes messages to queue (mock recv_match)
- [x] 3.7.6 Test: recv_match with timeout raises TimeoutError
- [x] 3.7.7 Test: send method calls mav master send
- [x] 3.7.8 Create `tests/unit/test_heartbeat.py`
- [x] 3.7.9 Test: heartbeat monitor healthy when heartbeat received within timeout
- [x] 3.7.10 Test: heartbeat monitor unhealthy on timeout
- [x] 3.7.11 Test: heartbeat send periodic interval
- [x] 3.7.12 Create `tests/unit/test_telemetry.py` (comms)
- [x] 3.7.13 Test: GLOBAL_POSITION_INT → GeoPosition scale conversion
- [x] 3.7.14 Test: ATTITUDE → AttitudeData conversion
- [x] 3.7.15 Test: VFR_HUD → SpeedData conversion
- [x] 3.7.16 Test: SYS_STATUS → BatteryData conversion
- [x] 3.7.17 Test: HEARTBEAT → SystemStatus conversion
- [x] 3.7.18 Test: unknown message type handled gracefully
- [x] 3.7.19 Create `tests/unit/test_messages.py`
- [x] 3.7.20 Test: send_command_long sends correct MAVLink message
- [x] 3.7.21 Test: wait_for_message timeout behavior

### 3.8 SITL Environment (Phase 3b)

- [x] 3.8.1 Create `scripts/setup_sitl.sh` — ArduPilot SITL install script
- [x] 3.8.2 Create `scripts/run_sitl.sh` — One-click SITL launch script
- [x] 3.8.3 Create `docs/sitl_setup.md` — SITL setup documentation
- [x] 3.8.4 Create `tests/integration/__init__.py`
- [x] 3.8.5 Create `tests/integration/conftest.py` — SITL fixture (auto start/stop)
- [x] 3.8.6 Implement SITL fixture: start SITL in subprocess, wait for UDP port
- [x] 3.8.7 Implement SITL fixture: teardown kills SITL subprocess
- [x] 3.8.8 Create `tests/integration/test_sitl_connection.py`
- [x] 3.8.9 Test: connect to SITL, receive HEARTBEAT
- [x] 3.8.10 Test: telemetry parsing with real SITL data
- [x] 3.8.11 Test: heartbeat timeout detection by disconnecting SITL

### 3.9 Exception Updates

- [x] 3.9.1 Add `CommsError` subclasses: `MavlinkConnectionError`, `HeartbeatTimeoutError`, `MessageTimeoutError`
- [x] 3.9.2 Add `MissionUploadError` to exceptions.py

### 3.10 Phase 3 Verification & Commit

- [x] 3.10.1 Run incremental unit tests for all Phase 3 modules (`pytest tests/unit/test_connection.py`, etc.)
- [x] 3.10.2 Perform full project dry-run for Phase 3 components.
- [x] 3.10.3 IF BUG DETECTED: Insert debug iteration block, fix bugs until dry-run passes.
- [x] 3.10.4 Git Commit Phase 3 changes with message: `feat(comms): 完成阶段3 MAVLink底层通信模块实现与基本SITL集成`

### 5.19 Phase 5 Verification & Commit

- [x] 5.19.1 Run incremental unit tests for all Phase 5 modules (Flight, Navigation).
- [x] 5.19.2 Perform full project dry-run (SITL Takeoff/Scan execution).
- [x] 5.19.3 IF BUG DETECTED: Insert debug iteration block.
- [x] 5.19.4 Git Commit Phase 5 changes with message: `feat(flight): 完成阶段5 飞行控制、扫描与降落业务状态机`

---

## Phase 4: State Machine Engine + Safety Monitor

### 4.1 Core Package Scaffold

- [x] 4.1.1 Create `src/striker/core/__init__.py`
- [x] 4.1.2 Create `src/striker/core/states/__init__.py` with state registry

### 4.2 Events

- [x] 4.2.1 Create `src/striker/core/events.py`
- [x] 4.2.2 Define `SystemEvent` enum (INIT_COMPLETE, SHUTDOWN)
- [x] 4.2.3 Define `FlightEvent` enum (TAKEOFF_COMPLETE, LANDING_COMPLETE, MISSION_LOADED, ARM_SUCCESS)
- [x] 4.2.4 Define `ScanEvent` enum (SCAN_COMPLETE, LOITER_TIMEOUT, TARGET_ACQUIRED)
- [x] 4.2.5 Define `OverrideEvent` dataclass
- [x] 4.2.6 Define `EmergencyEvent` dataclass with reason field
- [x] 4.2.7 Define `Transition` dataclass (target_state, reason)

### 4.3 Base State

- [x] 4.3.1 Create `src/striker/core/states/base.py`
- [x] 4.3.2 Define `BaseState` ABC with abstract `on_enter(context)`, `execute(context)`, `on_exit(context)`
- [x] 4.3.3 Implement `handle(event) → Optional[Transition]` base method
- [x] 4.3.4 Add state name property and logging mixin

### 4.4 Context

- [x] 4.4.1 Create `src/striker/core/context.py`
- [x] 4.4.2 Define `MissionContext` with subsystem reference fields
- [x] 4.4.3 Add mutable state fields: current_position, scan_cycle_count, last_target
- [x] 4.4.4 Add field_profile field (from Phase 2)
- [x] 4.4.5 Implement `update_position(pos)` method
- [x] 4.4.6 Implement `update_target(target)` method

### 4.5 FSM Engine

- [x] 4.5.0 Use Context7 MCP to query `python-statemachine` declarative syntax and edge cases
- [x] 4.5.1 Create `src/striker/core/machine.py`
- [x] 4.5.2 Define `MissionStateMachine` using `python-statemachine` declarative syntax (`State`, `Event`)
- [x] 4.5.3 Set `rtc=False` on the state machine to prevent run-to-completion deadlocks in async contexts
- [x] 4.5.4 Support delayed initialization explicitly via `activate_initial_state()` integration
- [x] 4.5.5 Implement global transition handlers via `python-statemachine` event hooks for OverrideEvent / EmergencyEvent
- [x] 4.5.6 Implement transition execution using `on_enter_` and `on_exit_` decorators/methods
- [x] 4.5.7 Implement transition logging via structlog hooking into the router
- [x] 4.5.8 Implement `async run()` main loop to pump events safely
- [x] 4.5.9 Add robust exception handling inside state transitions (Code Robustness)
- [x] 4.5.10 Implement `current_state` property wrapping statemachine state

### 4.6 Base States

- [x] 4.6.1 Create `src/striker/core/states/init.py`
- [x] 4.6.2 Implement InitState: on_enter logs system start, execute waits for INIT_COMPLETE
- [x] 4.6.3 Implement InitState: transition to PREFLIGHT on INIT_COMPLETE event
- [x] 4.6.4 Create `src/striker/core/states/override.py`
- [x] 4.6.5 Implement OverrideState: terminal state, on_enter logs human takeover (RL-03)
- [x] 4.6.6 Implement OverrideState: no automatic recovery possible
- [x] 4.6.7 Create `src/striker/core/states/emergency.py`
- [x] 4.6.8 Implement EmergencyState: trigger emergency landing procedure
- [x] 4.6.9 Implement EmergencyState: log emergency reason from event data

### 4.7 FSM Unit Tests

- [x] 4.7.0 Create `tests/fixtures/` directory for test mock data
- [x] 4.7.1 Create `tests/unit/test_state_machine.py`
- [x] 4.7.2 Test: register multiple states
- [x] 4.7.3 Test: INIT → no-op event stays INIT
- [x] 4.7.4 Test: INIT → OverrideEvent → OVERRIDE transition
- [x] 4.7.5 Test: any state → EmergencyEvent → EMERGENCY
- [x] 4.7.6 Test: OverrideEvent from any state → OVERRIDE (global interceptor)
- [x] 4.7.7 Test: on_exit called before on_enter during transition
- [x] 4.7.8 Test: transition logged via structlog
- [x] 4.7.9 Test: MissionContext update_position works
- [x] 4.7.10 Test: MissionContext update_target works

### 4.8 Safety — Geofence

- [x] 4.8.1 Create `src/striker/safety/__init__.py`
- [x] 4.8.2 Create `src/striker/safety/geofence.py`
- [x] 4.8.3 Implement `Geofence.__init__(polygon_points)` from FieldProfile boundary
- [x] 4.8.4 Implement `is_inside(lat, lon) → bool` using ray-casting algorithm
- [x] 4.8.5 Implement `distance_to_boundary(lat, lon) → float` proximity helper

### 4.9 Safety — Checks

- [x] 4.9.1 Create `src/striker/safety/checks.py`
- [x] 4.9.2 Implement `BatteryCheck`: voltage < threshold → EmergencyEvent
- [x] 4.9.3 Implement `GPSCheck`: fix type and satellite count validation
- [x] 4.9.4 Implement `HeartbeatCheck`: delegate to HeartbeatMonitor.is_healthy
- [x] 4.9.5 Implement `AirspeedCheck`: below stall speed → warning
- [x] 4.9.6 Implement `GeofenceCheck`: outside boundary → EmergencyEvent
- [x] 4.9.7 Make all check thresholds configurable via settings

### 4.10 Safety — Override Detector

- [x] 4.10.1 Create `src/striker/safety/override_detector.py`
- [x] 4.10.2 Implement `OverrideDetector` monitoring FC mode changes
- [x] 4.10.3 Detect mode switch to MANUAL → emit OverrideEvent
- [x] 4.10.4 Configurable set of modes that trigger override

### 4.11 Safety — Monitor

- [x] 4.11.1 Create `src/striker/safety/monitor.py`
- [x] 4.11.2 Implement `SafetyMonitor.__init__()` with all checks and context
- [x] 4.11.3 Implement `async run()` periodic check loop with configurable interval
- [x] 4.11.4 Implement check result aggregation and event emission
- [x] 4.11.5 Implement graceful shutdown handling

### 4.12 Safety Unit Tests

- [x] 4.12.1 Create `tests/unit/test_safety.py`
- [x] 4.12.2 Test: BatteryCheck triggers EmergencyEvent on low voltage
- [x] 4.12.3 Test: BatteryCheck passes on normal voltage
- [x] 4.12.4 Test: GPSCheck fails on no-fix
- [x] 4.12.5 Test: GeofenceCheck detects position outside fence
- [x] 4.12.6 Test: GeofenceCheck passes for position inside fence
- [x] 4.12.7 Test: OverrideDetector emits event on MANUAL mode switch
- [x] 4.12.8 Test: SafetyMonitor runs all checks in sequence
- [x] 4.12.9 Test: SafetyMonitor emits EmergencyEvent when check fails
- [x] 4.12.10 Create `tests/unit/test_geofence.py`
- [x] 4.12.11 Test: Geofence.is_inside for known interior point
- [x] 4.12.12 Test: Geofence.is_inside for known exterior point
- [x] 4.12.13 Test: Geofence.is_inside for point on boundary

### 4.13 Flight Recorder

- [x] 4.13.1 Create `src/striker/telemetry/flight_recorder.py`
- [x] 4.13.2 Implement `FlightRecorder.__init__()` with output path, fields config
- [x] 4.13.3 Implement CSV header writing on file open
- [x] 4.13.4 Implement `async run()` periodic telemetry snapshot writing
- [x] 4.13.5 Implement configurable sample rate from settings
- [x] 4.13.6 Implement auto-flush on shutdown

### 4.14 Flight Recorder Tests

- [x] 4.14.1 Create `tests/unit/test_flight_recorder.py`
- [x] 4.14.2 Test: CSV file created with correct headers
- [x] 4.14.3 Test: telemetry data rows written correctly
- [x] 4.14.4 Test: auto-flush on stop
- [x] 4.14.5 Test: custom output directory from settings

### 4.15 GCS Reporter (Reserved)

- [x] 4.15.1 Create `src/striker/telemetry/reporter.py`
- [x] 4.15.2 Define `GcsReporter` Protocol with reserved interface (no implementation)

### 4.16 Phase 4 Verification & Commit

- [x] 4.16.1 Run incremental unit tests for all Phase 4 modules (FSM, Safety, Telemetry).
- [x] 4.16.2 Perform full project dry-run for Phase 4 components.
- [x] 4.16.3 IF BUG DETECTED: Insert debug iteration block for FSM/Safety.
- [x] 4.16.4 Git Commit Phase 4 changes with message: `feat(core): 完成阶段4 状态机引擎与安全检查模块，重构为python-statemachine声明式`

---

## Phase 5: Flight Command Layer + Scan/Landing + Business States

### 5.1 Flight Package Scaffold

- [x] 5.1.1 Create `src/striker/flight/__init__.py`

### 5.2 Flight Modes

- [x] 5.2.1 Create `src/striker/flight/modes.py`
- [x] 5.2.2 Define `ArduPlaneMode` enum (MANUAL, FBWA, AUTO, GUIDED, LOITER, RTL, CRUISE)
- [x] 5.2.3 Add mode name ↔ MAVLink mode ID mapping

### 5.3 Flight Controller

- [x] 5.3.1 Create `src/striker/flight/controller.py`
- [x] 5.3.2 Implement `FlightController.__init__()` with MAVLinkConnection reference
- [x] 5.3.3 Implement `async arm()` — send ARM command with pre-arm verification
- [x] 5.3.4 Implement `async takeoff(alt_m)` — set AUTO mode, send NAV_TAKEOFF
- [x] 5.3.5 Implement `async goto(lat, lon, alt_m)` — GUIDED mode + SET_POSITION_TARGET
- [x] 5.3.6 Implement `async set_mode(mode)` — mode switch with ACK verification
- [x] 5.3.7 Implement `async set_speed(speed_mps)` — MAV_CMD_DO_CHANGE_SPEED
- [x] 5.3.8 Implement GPS validation in all coordinate-accepting methods (RL-05)
- [x] 5.3.9 Add robustness: Handle GPS signal loss or timeout during GUIDED coordinate commands

### 5.4 Navigation — Waypoint Generation

- [x] 5.4.1 Create `src/striker/flight/navigation.py`
- [x] 5.4.2 Implement scan waypoint generation from FieldProfile.scan_waypoints
- [x] 5.4.3 Implement NAV_WAYPOINT mission item creation helper
- [x] 5.4.4 Implement NAV_TAKEOFF mission item creation helper
- [x] 5.4.5 Implement DO_LAND_START mission item creation helper
- [x] 5.4.6 Implement NAV_LAND mission item creation helper
- [x] 5.4.7 Implement waypoint sequence builder (scan + landing combined)

### 5.5 Mission Upload Protocol

- [x] 5.5.1 Implement `async upload_mission(items)` full protocol
- [x] 5.5.2 Step 1: MISSION_CLEAR_ALL send + ACK verification
- [x] 5.5.3 Step 2: MISSION_COUNT send with item count
- [x] 5.5.4 Step 3: MISSION_REQUEST_INT response loop (by index)
- [x] 5.5.5 Step 4: Final MISSION_ACK verification (type == ACCEPTED)
- [x] 5.5.6 Implement per-step timeout with MissionUploadError on failure
- [x] 5.5.7 Implement `async upload_scan_waypoints(field_profile)` convenience wrapper
- [x] 5.5.8 Implement `async upload_landing_sequence(field_profile)` convenience wrapper

### 5.6 Landing Sequence

- [x] 5.6.1 Create `src/striker/flight/landing_sequence.py`
- [x] 5.6.2 Implement landing sequence generation from FieldProfile.landing config
- [x] 5.6.3 Generate DO_LAND_START → approach waypoint → NAV_LAND sequence
- [x] 5.6.4 Validate landing parameters from field profile before generation

### 5.7 Business State — PreflightState

- [x] 5.7.1 Create `src/striker/core/states/preflight.py`
- [x] 5.7.2 Implement PreflightState.on_enter: upload geofence to FC
- [x] 5.7.3 Implement PreflightState.on_enter: upload landing sequence to FC
- [x] 5.7.4 Implement PreflightState.on_enter: reset scan_cycle_count to 0
- [x] 5.7.5 Implement PreflightState.execute: verify uploads complete
- [x] 5.7.6 Implement PreflightState: transition to TAKEOFF on success

### 5.8 Business State — TakeoffState

- [x] 5.8.1 Create `src/striker/core/states/takeoff.py`
- [x] 5.8.2 Implement TakeoffState.on_enter: send ARM command
- [x] 5.8.3 Implement TakeoffState.on_enter: send takeoff command with target altitude
- [x] 5.8.4 Implement TakeoffState.execute: monitor altitude, wait for target
- [x] 5.8.5 Implement TakeoffState: transition to SCAN on altitude reached

### 5.9 Business State — ScanState

- [x] 5.9.1 Create `src/striker/core/states/scan.py`
- [x] 5.9.2 Implement ScanState.on_enter: increment scan_cycle_count
- [x] 5.9.3 Implement ScanState.on_enter: set AUTO mode for scan waypoint sequence
- [x] 5.9.4 Implement ScanState.execute: monitor waypoint progress via MISSION_ITEM_REACHED MAVLink messages
- [x] 5.9.5 Implement ScanState: detect scan completion → transition to LOITER
- [x] 5.9.6 Implement ScanState: log scan cycle number

### 5.10 Business State — LoiterState

- [x] 5.10.1 Create `src/striker/core/states/loiter.py`
- [x] 5.10.2 Implement LoiterState.on_enter: set LOITER mode with configured radius
- [x] 5.10.3 Implement LoiterState.on_enter: start timeout timer (loiter_timeout_s)
- [x] 5.10.4 Implement LoiterState.execute: check for target received from tracker
- [x] 5.10.5 Implement LoiterState: target received → transition to ENROUTE
- [x] 5.10.6 Implement LoiterState: timeout with cycle < max → transition to SCAN
- [x] 5.10.7 Implement LoiterState: timeout with cycle >= max → transition to FORCED_STRIKE

### 5.11 Business State — EnrouteState

- [x] 5.11.1 Create `src/striker/core/states/enroute.py`
- [x] 5.11.2 Implement EnrouteState.on_enter: GUIDED goto target coordinates
- [x] 5.11.3 Implement EnrouteState.execute: monitor distance to target
- [x] 5.11.4 Implement EnrouteState: approach distance reached → transition to APPROACH
- [x] 5.11.5 Implement EnrouteState: update target if tracker provides new data

### 5.12 Business State — LandingState

- [x] 5.12.1 Create `src/striker/core/states/landing.py`
- [x] 5.12.2 Implement LandingState.on_enter: trigger landing sequence
- [x] 5.12.3 Implement LandingState.execute: monitor for landing detection
- [x] 5.12.4 Implement LandingState: transition to COMPLETED on landing detected

### 5.13 Business State — CompletedState

- [x] 5.13.1 Create `src/striker/core/states/completed.py`
- [x] 5.13.2 Implement CompletedState.on_enter: log mission success
- [x] 5.13.3 Implement CompletedState.on_enter: stop flight recorder
- [x] 5.13.4 Implement CompletedState: terminal state, no transitions out

### 5.14 Flight Controller Tests

- [x] 5.14.1 Create `tests/unit/test_flight_controller.py`
- [x] 5.14.2 Test: arm() sends correct MAVLink command
- [x] 5.14.3 Test: takeoff(alt) sets AUTO mode and NAV_TAKEOFF
- [x] 5.14.4 Test: goto(lat, lon, alt) uses GUIDED mode
- [x] 5.14.5 Test: set_mode verifies ACK
- [x] 5.14.6 Test: set_speed sends DO_CHANGE_SPEED
- [x] 5.14.7 Test: GPS validation rejects invalid coordinates
- [x] 5.14.8 Test: GPS validation accepts valid coordinates

### 5.15 Navigation Tests

- [x] 5.15.1 Create `tests/unit/test_navigation.py`
- [x] 5.15.2 Test: scan waypoint generation from field profile
- [x] 5.15.3 Test: NAV_WAYPOINT mission item fields correct
- [x] 5.15.4 Test: waypoint sequence builder produces correct order
- [x] 5.15.5 Test: landing sequence generation from field profile

### 5.16 Mission Upload Tests

- [x] 5.16.1 Create `tests/unit/test_mission_upload.py`
- [x] 5.16.2 Test: full upload protocol succeeds with mock FC
- [x] 5.16.3 Test: MISSION_CLEAR_ALL sent first
- [x] 5.16.4 Test: MISSION_COUNT correct
- [x] 5.16.5 Test: responds to MISSION_REQUEST_INT by index
- [x] 5.16.6 Test: final MISSION_ACK type == ACCEPTED
- [x] 5.16.7 Test: timeout on MISSION_REQUEST_INT raises MissionUploadError
- [x] 5.16.8 Test: rejected MISSION_ACK raises MissionUploadError

### 5.17 Business State Tests

- [x] 5.17.1 Create `tests/unit/test_states.py`
- [x] 5.17.2 Test: PreflightState resets scan_cycle_count
- [x] 5.17.3 Test: TakeoffState waits for altitude
- [x] 5.17.4 Test: ScanState increments cycle counter
- [x] 5.17.5 Test: ScanState completes → LOITER transition
- [x] 5.17.6 Test: LoiterState timeout cycle < max → SCAN transition
- [x] 5.17.7 Test: LoiterState timeout cycle >= max → FORCED_STRIKE transition
- [x] 5.17.8 Test: LoiterState target received → ENROUTE transition
- [x] 5.17.9 Test: EnrouteState approach distance → APPROACH transition
- [x] 5.17.10 Test: LandingState landing detected → COMPLETED transition
- [x] 5.17.11 Test: CompletedState is terminal
- [x] 5.17.12 Test: full state chain INIT→PREFLIGHT→TAKEOFF→SCAN→LOITER→ENROUTE→LANDING→COMPLETED

### 5.18 SITL Integration Tests

- [x] 5.18.1 Create `tests/integration/test_sitl_takeoff.py`
- [x] 5.18.2 Test: SITL ARM → AUTO takeoff → climb to altitude
- [x] 5.18.3 Create `tests/integration/test_sitl_scan_loiter.py`
- [x] 5.18.4 Test: SITL SCAN follows field profile waypoints
- [x] 5.18.5 Test: SITL SCAN complete → auto-switch to LOITER
- [x] 5.18.6 Test: SITL LOITER timeout → back to SCAN

### 5.19 Phase 5 Verification & Commit

- [x] 5.19.1 Run incremental unit tests for all Phase 5 modules (Flight, Navigation).
- [x] 5.19.2 Perform full project dry-run (SITL Takeoff/Scan execution).
- [x] 5.19.3 IF BUG DETECTED: Insert debug iteration block.
- [x] 5.19.4 Git Commit Phase 5 changes with message: `feat(flight): 完成阶段5 飞行控制、扫描与降落业务状态机`

---

## Phase 6: External Solver Link + Coordinate Utilities

### 6.1 Vision Package Scaffold

- [x] 6.1.1 Create `src/striker/vision/__init__.py` with receiver registry

### 6.2 Vision Models

- [x] 6.2.1 Create `src/striker/vision/models.py`
- [x] 6.2.2 Define `GpsTarget` dataclass (lat, lon, confidence, timestamp)
- [x] 6.2.3 Implement GpsTarget validation: lat [-90, 90], lon [-180, 180], confidence [0, 1]
- [x] 6.2.4 Implement `validate_gps()` function (RL-05)

### 6.3 VisionReceiver Protocol

- [x] 6.3.1 Create `src/striker/vision/protocol.py`
- [x] 6.3.2 Define `VisionReceiver` Protocol with start/stop/get_latest

### 6.3b Shared Memory Receiver

- [x] 6.3b.1 Create `src/striker/vision/shared_mem_receiver.py` (Reserved Interface)
- [x] 6.3b.2 Define base stubs for reading targets via SHM

### 6.4 TCP Receiver

- [x] 6.4.1 Create `src/striker/vision/tcp_receiver.py`
- [x] 6.4.2 Implement `TcpReceiver.__init__()` with host/port config
- [x] 6.4.3 Implement `async start()` — create TCP server socket
- [x] 6.4.4 Implement connection handler — parse JSON messages
- [x] 6.4.5 Implement `get_latest() → GpsTarget | None`
- [x] 6.4.6 Implement `async stop()` — close server and connections
- [x] 6.4.7 Handle malformed messages with WARNING log

### 6.5 UDP Receiver

- [x] 6.5.1 Create `src/striker/vision/udp_receiver.py`
- [x] 6.5.2 Implement `UdpReceiver.__init__()` with host/port config
- [x] 6.5.3 Implement `async start()` — create UDP socket, start listen coroutine
- [x] 6.5.4 Implement datagram handler — parse JSON messages
- [x] 6.5.5 Implement `get_latest() → GpsTarget | None`
- [x] 6.5.6 Implement `async stop()` — close socket

### 6.6 Target Tracker

- [x] 6.6.1 Create `src/striker/vision/tracker.py`
- [x] 6.6.2 Implement `TargetTracker.__init__()` with window_size config
- [x] 6.6.3 Implement `push(lat, lon)` — append to deque windows
- [x] 6.6.4 Implement `get_smoothed_target()` — median filter using statistics.median
- [x] 6.6.5 Implement frequency detection logic
- [x] 6.6.6 Implement stale detection: configurable timeout marks target expired
- [x] 6.6.7 Implement `last_update_time` tracking
- [x] 6.6.8 Implement adaptive mode: 0Hz / single / low-freq / high-freq handling

### 6.7 Vision Tests

- [x] 6.7.1 Create `tests/unit/test_vision_receiver.py`
- [x] 6.7.2 Test: TcpReceiver parses valid JSON message → GpsTarget
- [x] 6.7.3 Test: TcpReceiver rejects malformed JSON with WARNING
- [x] 6.7.4 Test: UdpReceiver parses valid JSON message → GpsTarget
- [x] 6.7.5 Test: GpsTarget validation rejects lat=200
- [x] 6.7.6 Test: GpsTarget validation rejects lon=361
- [x] 6.7.7 Test: GpsTarget validation rejects confidence=1.5
- [x] 6.7.8 Test: GpsTarget validation accepts valid coordinates
- [x] 6.7.9 Create `tests/unit/test_tracker.py`
- [x] 6.7.10 Test: single push → target returned immediately
- [x] 6.7.11 Test: high-frequency push → median smoothed output
- [x] 6.7.12 Test: low-frequency push → each update adopted
- [x] 6.7.13 Test: no data → get_smoothed_target returns None
- [x] 6.7.14 Test: stale detection after timeout → target expired

### 6.8 Utils Package Scaffold

- [x] 6.8.1 Create `src/striker/utils/__init__.py`

### 6.9 Geo Utilities

- [x] 6.9.1 Create `src/striker/utils/geo.py`
- [x] 6.9.2 Implement `haversine_distance(lat1, lon1, lat2, lon2) → float` (meters)
- [x] 6.9.3 Implement `calculate_bearing(lat1, lon1, lat2, lon2) → float` (degrees)
- [x] 6.9.4 Implement `destination_point(lat, lon, bearing, distance) → tuple[float, float]`
- [x] 6.9.5 Implement `validate_gps(lat, lon) → bool` — range checks (RL-05)

### 6.10 Coordinate Converter

- [x] 6.10.1 Create `src/striker/utils/converter.py`
- [x] 6.10.2 Implement `CoordConverter.__init__(ref_lat, ref_lon)` with reference point
- [x] 6.10.3 Implement `ned_to_gps(north_m, east_m) → tuple[float, float]`
- [x] 6.10.4 Implement `gps_to_ned(lat, lon) → tuple[float, float]`
- [x] 6.10.4b Implement `map_pixel_to_gps(pixel_x, pixel_y, camera_params) → tuple[float, float]`
- [x] 6.10.5 Handle Earth radius scaling by latitude

### 6.11 Point-in-Polygon

- [x] 6.11.1 Create `src/striker/utils/point_in_polygon.py`
- [x] 6.11.2 Implement `point_in_polygon(lat, lon, polygon) → bool` using ray-casting
- [x] 6.11.3 Handle edge cases: point on boundary, point on vertex
- [x] 6.11.4 Optimize for GPS coordinate polygons

### 6.12 Forced Strike Point

- [x] 6.12.1 Create `src/striker/utils/forced_strike_point.py`
- [x] 6.12.2 Implement `generate_forced_strike_point(polygon, buffer_m) → tuple[float, float]`
- [x] 6.12.3 Implement bounding box rejection sampling inside polygon
- [x] 6.12.4 Implement safety buffer exclusion zone
- [x] 6.12.5 Implement point_in_polygon verification of generated point (RL-10)
- [x] 6.12.6 Add deterministic seeding option for reproducibility

### 6.13 Unit Conversions

- [x] 6.13.1 Create `src/striker/utils/units.py`
- [x] 6.13.2 Implement deg_to_rad / rad_to_deg
- [x] 6.13.3 Implement mps_to_kmh / kmh_to_mps
- [x] 6.13.4 Implement meters_to_feet / feet_to_meters

### 6.14 Timing Utilities

- [x] 6.14.1 Create `src/striker/utils/timing.py`
- [x] 6.14.2 Implement `precise_timestamp() → float` (monotonic clock)
- [x] 6.14.3 Implement `RateLimiter` class for periodic operations

### 6.15 Utils Tests

- [x] 6.15.1 Create `tests/unit/test_geo.py`
- [x] 6.15.2 Test: haversine_distance known answer (e.g., ~111km per degree)
- [x] 6.15.3 Test: calculate_bearing north, south, east, west
- [x] 6.15.4 Test: destination_point known answer
- [x] 6.15.5 Test: validate_gps accepts valid, rejects invalid
- [x] 6.15.6 Create `tests/unit/test_converter.py`
- [x] 6.15.7 Test: NED(100m N, 50m E) → correct GPS offset (known answer)
- [x] 6.15.8 Test: round-trip NED → GPS → NED within tolerance
- [x] 6.15.9 Test: CoordConverter at different latitudes
- [x] 6.15.10 Create `tests/unit/test_point_in_polygon.py`
- [x] 6.15.11 Test: point inside polygon → True
- [x] 6.15.12 Test: point outside polygon → False
- [x] 6.15.13 Test: point on edge handling
- [x] 6.15.14 Test: concave polygon
- [x] 6.15.15 Create `tests/unit/test_forced_strike_point.py`
- [x] 6.15.16 Test: generate 1000 points, all inside polygon
- [x] 6.15.17 Test: generated points outside safety buffer
- [x] 6.15.18 Test: all generated points pass point_in_polygon verification
- [x] 6.15.19 Test: deterministic seeding produces same point
- [x] 6.15.20 Create `tests/unit/test_units.py`
- [x] 6.15.21 Test: all conversion functions round-trip correctly
- [x] 6.15.22 Create `tests/unit/test_timing.py`
- [x] 6.15.23 Test: precise_timestamp monotonically increasing
- [x] 6.15.24 Test: RateLimiter enforces interval

### 6.16 Phase 6 Verification & Commit

- [x] 6.16.1 Run incremental unit tests for Phase 6 modules (Vision, Utils).
- [x] 6.16.2 Perform full project dry-run.
- [x] 6.16.3 IF BUG DETECTED: Insert debug iteration block.
- [x] 6.16.4 Git Commit Phase 6 changes with message: `feat(vision): 完成阶段6 视觉目标接收器与坐标转换工具库`

---

## Phase 7: Payload System

### 7.1 Payload Package Scaffold

- [x] 7.1.1 Create `src/striker/payload/__init__.py` with release controller registry

### 7.2 Payload Models

- [x] 7.2.1 Create `src/striker/payload/models.py`
- [x] 7.2.2 Define `BallisticParams` dataclass (gravity, default altitude, etc.)
- [x] 7.2.3 Define `ReleaseConfig` dataclass (method, channel, pwm_open, pwm_close, gpio_pin, gpio_active_high)

### 7.3 Release Controller Protocol

- [x] 7.3.1 Create `src/striker/payload/protocol.py`
- [x] 7.3.2 Define `ReleaseController` Protocol with: `async arm()`, `async release()`, `is_armed: bool`, `is_released: bool`

### 7.4 Ballistic Solver

- [x] 7.4.1 Create `src/striker/payload/ballistics.py`
- [x] 7.4.2 Implement `BallisticCalculator.__init__()` with physical params
- [x] 7.4.3 Implement fall time calculation: `t_fall = sqrt(2h/g)`
- [x] 7.4.4 Implement displacement with wind: `d_north = (vel_n + wind_n) * t_fall`
- [x] 7.4.5 Implement bearing calculation from displacement
- [x] 7.4.6 Implement release point via geopy geodesic reverse projection
- [x] 7.4.7 Implement `calculate_release_point()` combining all steps
- [x] 7.4.8 Handle edge case: altitude <= 0 returns target unchanged
- [x] 7.4.9 Add velocity decomposition from ground speed + heading

### 7.5 MAVLink Release

- [x] 7.5.1 Create `src/striker/payload/mavlink_release.py`
- [x] 7.5.2 Implement `MavlinkRelease.__init__()` with connection and config
- [x] 7.5.3 Implement `async trigger()` — send DO_SET_SERVO command
- [x] 7.5.4 Implement ACK verification loop filtering for DO_SET_SERVO
- [x] 7.5.5 Implement timeout handling on ACK wait
- [x] 7.5.6 Implement DRY_RUN mode: skip + log

### 7.6 GPIO Release

- [x] 7.6.1 Create `src/striker/payload/gpio_release.py`
- [x] 7.6.2 Implement `GpioRelease.__init__()` with pin config
- [x] 7.6.3 Implement `async trigger()` — gpiod line set value
- [x] 7.6.4 Implement DRY_RUN mode: skip + log
- [x] 7.6.5 Handle gpiod import gracefully on non-GPIO platforms

### 7.6b Sequenced Release

- [x] 7.6b.1 Create `src/striker/payload/sequenced_release.py` (Reserved Interface)
- [x] 7.6b.2 Define interval/pattern-based multi-drop stubs

### 7.7 Approach State

- [x] 7.7.1 Create `src/striker/core/states/approach.py`
- [x] 7.7.2 Implement ApproachState.on_enter: calculate release point via ballistics
- [x] 7.7.3 Implement ApproachState.on_enter: GUIDED goto release point
- [x] 7.7.4 Implement ApproachState.execute: monitor distance to release point
- [x] 7.7.5 Implement ApproachState: on arrival → transition to RELEASE

### 7.8 Release State

- [x] 7.8.1 Create `src/striker/core/states/release.py`
- [x] 7.8.2 Implement ReleaseState.on_enter: trigger release controller
- [x] 7.8.3 Implement ReleaseState: verify release success
- [x] 7.8.4 Implement ReleaseState: transition to LANDING

### 7.9 Forced Strike State

- [x] 7.9.1 Create `src/striker/core/states/forced_strike.py`
- [x] 7.9.2 Implement ForcedStrikeState.on_enter: generate random point via forced_strike_point
- [x] 7.9.3 Implement ForcedStrikeState.on_enter: validate point with point_in_polygon (RL-10)
- [x] 7.9.4 Implement ForcedStrikeState.on_enter: GUIDED goto forced strike point
- [x] 7.9.5 Implement ForcedStrikeState.execute: monitor arrival at point
- [x] 7.9.6 Implement ForcedStrikeState: on arrival → trigger release
- [x] 7.9.7 Implement ForcedStrikeState: after release → transition to LANDING
- [x] 7.9.8 Implement DRY_RUN mode: skip actual release, log generated point

### 7.10 Payload Tests

- [x] 7.10.1 Create `tests/unit/test_ballistics.py`
- [x] 7.10.2 Test: KAT #1 — 50m alt, 20m/s N, 0 wind → ~63.9m lead (error < 0.1m)
- [x] 7.10.3 Test: KAT #2 — 100m alt, 25m/s E, 5m/s W wind → ~142.5m lead (error < 0.1m)
- [x] 7.10.4 Test: KAT #3 — 30m alt, 15m/s NE, 0 wind → ~37.1m lead (error < 0.1m)
- [x] 7.10.5 Test: altitude 0 returns target unchanged
- [x] 7.10.6 Test: negative altitude raises or returns target
- [x] 7.10.7 Test: pure north displacement
- [x] 7.10.8 Test: pure east displacement
- [x] 7.10.9 Test: wind compensation correct direction
- [x] 7.10.10 Create `tests/unit/test_release.py`
- [x] 7.10.11 Test: MavlinkRelease sends DO_SET_SERVO with correct params
- [x] 7.10.12 Test: MavlinkRelease verifies COMMAND_ACK result
- [x] 7.10.13 Test: MavlinkRelease timeout on no ACK
- [x] 7.10.14 Test: GpioRelease calls gpiod correctly
- [x] 7.10.15 Test: DRY_RUN mode skips trigger, logs action
- [x] 7.10.16 Create `tests/unit/test_forced_strike_state.py`
- [x] 7.10.17 Test: generates point inside geofence
- [x] 7.10.18 Test: generated point passes point_in_polygon validation
- [x] 7.10.19 Test: DRY_RUN mode skips release
- [x] 7.10.20 Test: transitions to LANDING after release

### 7.11 Phase 7 Verification & Commit

- [x] 7.11.1 Run incremental unit tests for Phase 7 modules (Payload, Ballistics).
- [x] 7.11.2 Perform full project dry-run payload drop simulation.
- [x] 7.11.3 IF BUG DETECTED: Insert debug iteration block.
- [x] 7.11.4 Git Commit Phase 7 changes with message: `feat(payload): 完成阶段7 投掷物释放控制与弹道解算模块`

---

## Phase 8: Full Mission Integration + CI/CD

### 8.1 Config Updates

- [x] 8.1.1 Add new fields to StrikerSettings: comms section (port, baud, transport)
- [x] 8.1.2 Add safety thresholds to StrikerSettings (battery_min_v, stall_speed, etc.)
- [x] 8.1.3 Add release config to StrikerSettings (method, channel, pwm, gpio_pin)
- [x] 8.1.4 Add vision config to StrikerSettings (receiver_type, host, port)
- [x] 8.1.5 Update config.example.json with all new fields
- [x] 8.1.6 Verify StrikerSettings loads with new defaults

### 8.2 App Main Loop

- [x] 8.2.1 Create `src/striker/app.py`
- [x] 8.2.2 Implement CLI argument parsing (--field, --dry-run, --list-fields)
- [x] 8.2.3 implement `async main()` — load settings and field profile
- [x] 8.2.4 Implement field profile validation on startup (RL-08), refuse launch on failure
- [x] 8.2.5 Implement subsystem initialization: MAVLinkConnection
- [x] 8.2.6 Implement subsystem initialization: SafetyMonitor
- [x] 8.2.7 Implement subsystem initialization: VisionReceiver (factory from config)
- [x] 8.2.8 Implement subsystem initialization: TargetTracker
- [x] 8.2.9 Implement subsystem initialization: FlightController
- [x] 8.2.10 Implement subsystem initialization: ReleaseController (factory from config)
- [x] 8.2.11 Implement subsystem initialization: BallisticCalculator
- [x] 8.2.12 Implement subsystem initialization: FlightRecorder
- [x] 8.2.13 Implement MissionContext creation with all subsystems
- [x] 8.2.14 Implement MissionStateMachine creation and state registration
- [x] 8.2.15 Implement async TaskGroup launch: conn.run, safety.run, vision.run, fsm.run, recorder.run
- [x] 8.2.16 Implement graceful shutdown on SIGINT/SIGTERM
- [x] 8.2.17 Update `src/striker/__main__.py` to call app.main()

### 8.3 Vision Receiver Factory

- [x] 8.3.1 Implement `create_vision_receiver(settings)` factory in vision/__init__.py
- [x] 8.3.2 Implement `create_release_controller(settings, conn)` factory in payload/__init__.py

### 8.4 Deployment Scripts

- [x] 8.4.1 Create `scripts/preflight_check.py` — standalone preflight validation
- [x] 8.4.2 Implement field profile validation in preflight check
- [x] 8.4.3 Implement connectivity check in preflight check
- [x] 8.4.4 Create `scripts/lint_registry.py` — REGISTRY.md sync check
- [x] 8.4.5 Implement public symbol extraction from source
- [x] 8.4.6 Implement REGISTRY.md parsing and comparison
- [x] 8.4.7 Create `scripts/check_pkg_versions.py` — pkg version consistency
- [x] 8.4.8 Implement pkg pyproject.toml version reading
- [x] 8.4.9 Implement version comparison logic
- [x] 8.4.10 Create `scripts/setup_rpi5.sh` — RPi5 deployment script
- [x] 8.4.11 Implement dependency installation for RPi5
- [x] 8.4.12 Implement service configuration for RPi5

### 8.5 CI/CD Pipeline

- [x] 8.5.1 Create `.github/workflows/ci.yml`
- [x] 8.5.2 Configure Python 3.13 environment
- [x] 8.5.3 Configure uv installation in CI
- [x] 8.5.4 Implement Stage 1: ruff check lint
- [x] 8.5.5 Implement Stage 2: mypy --strict type check
- [x] 8.5.6 Implement Stage 3: pytest unit tests
- [x] 8.5.7 Implement Stage 4: registry lint + pkg version check
- [x] 8.5.8 Implement Stage 5: SITL integration tests (scheduled trigger)
- [x] 8.5.9 Configure caching for uv dependencies

### 8.6 Integration Tests

- [x] 8.6.1 Create `tests/integration/test_sitl_full_mission.py`
- [x] 8.6.2 Test: normal path — ARM→TAKEOFF→SCAN→LOITER→(sim coords)→ENROUTE→APPROACH→RELEASE(dry)→LANDING→COMPLETED
- [x] 8.6.3 Test: degradation path — 3x LOITER timeout → FORCED_STRIKE → LANDING → COMPLETED
- [x] 8.6.4 Test: human override — SITL manual mode switch → OVERRIDE detection
- [x] 8.6.5 Test: field profile loading at startup
- [x] 8.6.6 Test: field profile switch via --field parameter

### 8.7 Documentation

- [x] 8.7.1 Create `docs/architecture.md` — system architecture overview
- [x] 8.7.2 Create `docs/config_reference.md` — full configuration reference
- [x] 8.7.3 Create `docs/field_profile.md` — field profile authoring guide
- [x] 8.7.4 Create `docs/states.md` — state machine documentation
- [x] 8.7.5 Create `docs/ballistics.md` — ballistic model documentation
- [x] 8.7.6 Create `docs/wiring.md` — hardware wiring documentation

### 8.8 REGISTRY Update

- [x] 8.8.1 Update REGISTRY.md with all new public symbols from Phase 3-8
- [x] 8.8.2 Verify lint_registry.py passes with updated registry

### 8.9 Final Validation

- [x] 8.9.1 Run `ruff check .` — zero errors
- [x] 8.9.2 Run `mypy src/ --strict` — zero errors
- [x] 8.9.3 Run `pytest tests/unit/` — all pass
- [x] 8.9.4 Verify no pymavlink imports outside comms/ (RL-04)
- [x] 8.9.5 Verify all GPS coords validated (RL-05)
- [x] 8.9.6 Verify no hardcoded parameters (RL-06)

### 8.10 Phase 8 Verification & Commit

- [x] 8.10.1 Run incremental unit tests for Phase 8 integration points.
- [x] 8.10.2 Perform full project dry-run for complete end-to-end mission loop in SITL.
- [x] 8.10.3 IF BUG DETECTED: Insert debug iteration block.
- [x] 8.10.4 Git Commit Phase 8 changes with message: `feat(app): 完成阶段8 完整应用集成，配置项完善及CLI入口`
