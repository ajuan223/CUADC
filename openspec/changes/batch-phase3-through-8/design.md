## Architecture Overview

This change implements Phases 3-8 of the Striker meta development plan as a layered architecture:

```
app.py (Phase 8 orchestration)
  ├── MissionStateMachine (Phase 4 FSM engine)
  │     ├── INIT, OVERRIDE, EMERGENCY (Phase 4 base states)
  │     ├── PREFLIGHT, TAKEOFF, SCAN, LOITER (Phase 5 states)
  │     ├── ENROUTE, LANDING, COMPLETED (Phase 5 states)
  │     ├── APPROACH, RELEASE (Phase 7 states)
  │     └── FORCED_STRIKE (Phase 7 degradation state)
  ├── SafetyMonitor (Phase 4 safety)
  │     ├── Geofence checking
  │     ├── Battery/GPS/heartbeat/airspeed checks
  │     └── Override detection
  ├── MAVLinkConnection (Phase 3 comms)
  │     ├── Async rx_loop + Queue dispatch
  │     ├── Heartbeat watchdog
  │     └── Telemetry parser (→ typed dataclasses)
  ├── FlightController (Phase 5 flight)
  │     ├── arm/takeoff/goto/set_mode/set_speed
  │     ├── Mission Upload Protocol
  │     └── Landing sequence generation
  ├── VisionReceiver (Phase 6 vision)
  │     ├── TCP/UDP receivers
  │     └── TargetTracker (adaptive smoothing)
  ├── BallisticCalculator (Phase 7 payload)
  ├── ReleaseController (Phase 7 payload)
  │     ├── MAVLink servo channel
  │     └── GPIO channel
  └── FlightRecorder (Phase 4 telemetry)
```

## Phase 3: MAVLink Communication Layer

### 3.1 Connection Management (`comms/connection.py`)

`MAVLinkConnection` wraps `pymavlink.mavutil.mavlink_connection` with async-compatible API:
- Constructor accepts transport URL (serial `/dev/serial0` or UDP `udp:127.0.0.1:14550`)
- `async connect()` — establishes connection, waits for first heartbeat
- `async run()` — starts rx_loop coroutine (Producer)
- `_rx_loop()` — `recv_match(blocking=False)` with 5ms sleep yield, pushes to `asyncio.Queue`
- `send(msg)` — thread-safe message send
- `async recv_match(type, timeout)` — consumer side, awaits from Queue with timeout
- Connection state tracking: DISCONNECTED → CONNECTING → CONNECTED → LOST
- All pymavlink imports confined to `comms/` package (RL-04)

### 3.2 Heartbeat Monitor (`comms/heartbeat.py`)

- Periodic heartbeat send (1Hz, configurable)
- Heartbeat receive watchdog using `asyncio.wait_for` with configurable timeout (default 3s)
- `heartbeat_event: asyncio.Event` cleared on timeout, set on receive
- `is_healthy: bool` property for health status
- Callback system for connection state changes

### 3.3 Message Types (`comms/messages.py`)

- Message type constants and enum for all used MAVLink messages
- `send_command_long()` wrapper with ACK verification
- `async wait_for_message(type, timeout)` helper

### 3.4 Telemetry Parser (`comms/telemetry.py`)

Typed dataclasses for all telemetry:
- `GeoPosition(lat: float, lon: float, alt_m: float, relative_alt_m: float)`
- `AttitudeData(roll_rad: float, pitch_rad: float, yaw_rad: float)`
- `SpeedData(airspeed_mps: float, groundspeed_mps: float)`
- `WindData(direction_deg: float, speed_mps: float)`
- `BatteryData(voltage_v: float, current_a: float, remaining_pct: int)`
- `SystemStatus(mode: str, armed: bool, system_status: int)`

Parsing done immediately in rx_loop routing, converting pymavlink weak types to strong types.

### 3.5 SITL Environment (Phase 3b)

- `scripts/setup_sitl.sh` — ArduPilot SITL installation
- `scripts/run_sitl.sh` — One-click SITL + MAVProxy launch
- `tests/integration/conftest.py` — SITL fixture with auto start/stop
- `docs/sitl_setup.md` — Setup documentation

## Phase 4: State Machine + Safety Monitor

### 4.1 FSM Engine (`core/machine.py`)

Uses `python-statemachine` library with `rtc=False` for async support:
- State registration dict + current state tracking
- `async process_event(event)` delegates to current state
- Global interceptors: OverrideEvent → OVERRIDE from any state; EmergencyEvent → EMERGENCY from any state
- Transition logging via structlog

### 4.2 Context (`core/context.py`)

`MissionContext` shared state container holding references to all subsystems:
- MAVLinkConnection, FlightController, SafetyMonitor
- VisionReceiver, TargetTracker, BallisticCalculator
- ReleaseController, FlightRecorder
- StrikerSettings, FieldProfile
- Mutable state: current position, scan_cycle_count, last_target, etc.

### 4.3 Events (`core/events.py`)

Event enum + data classes:
- SystemEvent (INIT_COMPLETE, SHUTDOWN)
- FlightEvent (TAKEOFF_COMPLETE, LANDING_COMPLETE, MISSION_LOADED)
- ScanEvent (SCAN_COMPLETE, LOITER_TIMEOUT, TARGET_ACQUIRED)
- OverrideEvent, EmergencyEvent (global interceptors)

### 4.4 Base State (`core/states/base.py`)

`BaseState` ABC with lifecycle:
- `async on_enter(context)` — setup when state becomes active
- `async execute(context)` — main state logic (called in loop)
- `async on_exit(context)` — cleanup when leaving state
- `handle(event) → Optional[Transition]`

### 4.5 Safety Monitor (`safety/monitor.py`)

Continuous coroutine running alongside FSM:
- Periodic check loop (configurable interval, default 1s)
- Individual checks in `safety/checks.py`:
  - Battery check: voltage < threshold → EmergencyEvent
  - GPS check: fix type, satellite count
  - Heartbeat check: delegates to heartbeat monitor status
  - Airspeed check: below stall speed → warning
  - Geofence check: position outside fence → EmergencyEvent
- Override detector (`safety/override_detector.py`): monitors FC mode changes → OverrideEvent

### 4.6 Geofence (`safety/geofence.py`)

- Polygon-based geofence from FieldProfile boundary
- `is_inside(lat, lon) → bool` using ray-casting algorithm
- `distance_to_boundary(lat, lon) → float` for proximity warnings

### 4.7 Flight Recorder (`telemetry/flight_recorder.py`)

- CSV recording with configurable fields and sample rate
- `async run()` coroutine writing periodic telemetry snapshots
- Auto-flush on shutdown

## Phase 5: Flight Commands + Business States

### 5.1 FlightController (`flight/controller.py`)

High-level flight command wrappers:
- `async arm()` — send ARM command with pre-arm checks
- `async takeoff(alt_m)` — set AUTO mode with NAV_TAKEOFF mission item
- `async goto(lat, lon, alt_m)` — GUIDED mode + SET_POSITION_TARGET
- `async set_mode(mode)` — mode switching with ACK verification
- `async set_speed(speed_mps)` — MAV_CMD_DO_CHANGE_SPEED
- `async upload_mission(items)` — full Mission Upload Protocol

### 5.2 Navigation (`flight/navigation.py`)

- Scan waypoint generation from FieldProfile scan_waypoints
- Mission item creation (MAVLink MAVLink_mission_item_int)
- Mission Upload Protocol wrapper:
  1. MISSION_CLEAR_ALL → MISSION_ACK
  2. MISSION_COUNT
  3. Respond to MISSION_REQUEST_INT per item by index
  4. Final MISSION_ACK verification

### 5.3 Landing Sequence (`flight/landing_sequence.py`)

- Fixed-wing landing sequence generation from FieldProfile landing config:
  - DO_LAND_START → approach waypoint → NAV_LAND
- Upload to FC before takeoff (part of PREFLIGHT state)

### 5.4 Business States

Each state implements BaseState lifecycle:

- **PreflightState**: upload geofence, upload landing sequence, reset scan_cycle_count, transition to TAKEOFF
- **TakeoffState**: send ARM + takeoff command, wait for altitude, transition to SCAN
- **ScanState**: set AUTO mode for scan waypoint sequence, increment scan_cycle_count, on completion → LOITER
- **LoiterState**: set LOITER mode, start timeout timer; on timeout: cycle < max → SCAN, cycle >= max → FORCED_STRIKE; on target → ENROUTE
- **EnrouteState**: GUIDED goto target coordinates, on approach distance → APPROACH
- **LandingState**: trigger landing sequence, wait for landing detection, → COMPLETED
- **CompletedState**: terminal state, log success, stop recorder

## Phase 6: External Solver + Coordinate Utilities

### 6.1 VisionReceiver Protocol (`vision/protocol.py`)

```python
class VisionReceiver(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def get_latest(self) -> GpsTarget | None: ...
```

### 6.2 TCP/UDP Receivers (`vision/tcp_receiver.py`, `vision/udp_receiver.py`)

- Async socket servers accepting coordinate messages
- Message format: JSON `{"lat": float, "lon": float, "confidence": float}`
- `GpsTarget` validation: lat [-90, 90], lon [-180, 180], confidence [0, 1]

### 6.3 TargetTracker (`vision/tracker.py`)

- Sliding window (deque) median filter for high-frequency input
- Adaptive frequency handling:
  - 0 Hz: maintain last state, no target
  - Single: immediately adopt
  - Low freq (<1Hz): each update adopted directly
  - High freq (>1Hz): N-frame median smoothing
- Stale detection: configurable timeout marks target as expired

### 6.4 Coordinate Utilities (`utils/`)

- `geo.py`: Haversine distance, bearing calculation, destination point
- `converter.py`: CoordConverter — NED ↔ WGS-84 using reference point
- `point_in_polygon.py`: Ray-casting algorithm, reused by safety geofence
- `forced_strike_point.py`: Random point generation inside polygon with buffer exclusion
- `units.py`: Degree/radian, m/s/km/h, meter/foot conversions
- `timing.py`: Precise timing helpers, rate limiter

## Phase 7: Payload System

### 7.1 BallisticCalculator (`payload/ballistics.py`)

Free-fall parabolic model with wind compensation:
- `t_fall = sqrt(2h / g)`
- Displacement: `d_north = (vel_n + wind_n) * t_fall`, `d_east = (vel_e + wind_e) * t_fall`
- Release point via `geopy.distance.geodesic` reverse projection
- Known-answer tests with error < 0.1m

### 7.2 ReleaseController (`payload/protocol.py`, `payload/mavlink_release.py`, `payload/gpio_release.py`)

Protocol:
```python
class ReleaseController(Protocol):
    async def trigger(self) -> bool: ...
```

- MAVLink: DO_SET_SERVO with COMMAND_ACK verification loop
- GPIO: gpiod direct drive with configurable pin
- Selection via `config.json` `release_method` field

### 7.3 Approach and Release States

- **ApproachState**: GUIDED mode to release point, on arrival → RELEASE
- **ReleaseState**: trigger release mechanism, verify completion, → LANDING
- **ForcedStrikeState**: generate random point via forced_strike_point, validate with point_in_polygon, fly to point, execute release, → LANDING

## Phase 8: Integration + CI/CD

### 8.1 Main Loop (`app.py`)

```python
async def main():
    settings = StrikerSettings()
    field_profile = load_field_profile(settings.field)
    # Initialize all subsystems
    # Create MissionContext
    # Create MissionStateMachine
    # Launch async tasks via TaskGroup
```

- Field profile validation at startup (failure refuses launch)
- Graceful shutdown handling
- CLI argument parsing (--field for field selection)

### 8.2 CI/CD (`.github/workflows/ci.yml`)

Multi-stage pipeline:
1. Lint: `ruff check .`
2. Type check: `mypy src/ --strict`
3. Unit tests: `pytest tests/unit/`
4. Registry lint + pkg version check
5. SITL integration tests (scheduled, heavy)

### 8.3 Scripts

- `scripts/preflight_check.py`: standalone preflight validation
- `scripts/lint_registry.py`: REGISTRY.md sync check
- `scripts/check_pkg_versions.py`: pkg/ version consistency
- `scripts/setup_rpi5.sh`: RPi5 deployment

### 8.4 Integration Tests

- `test_sitl_full_mission.py`: normal path (ARM → TAKEOFF → SCAN → LOITER → ENROUTE → APPROACH → RELEASE → LANDING → COMPLETED)
- Degradation path: 3x timeout → FORCED_STRIKE → LANDING → COMPLETED
- Human override test: manual mode switch → OVERRIDE detection

## Dependency Flow

```
Phase 3 (comms) → Phase 4 (FSM + safety) → Phase 5 (flight + states) → Phase 6 (vision + utils) → Phase 7 (payload) → Phase 8 (integration)
Phase 3b (SITL) — parallel with Phase 3
Phase 4c (recorder) — parallel with Phase 4a/4b
```

## Key Design Principles

1. **Protocol-first**: All cross-module interfaces defined as `typing.Protocol` before implementation
2. **pymavlink isolation**: Only `comms/` imports pymavlink (RL-04)
3. **Config-driven**: All parameters from StrikerSettings + FieldProfile (RL-06)
4. **Typed telemetry**: pymavlink messages → dataclasses at comms boundary
5. **Async-native**: All I/O via asyncio, pymavlink blocking calls wrapped in executor or non-blocking polling
6. **Test-every-layer**: Unit tests with mocks + SITL integration tests
