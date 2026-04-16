## Why

Phases 0-2 (scaffolding, governance, config/logging) are complete. The project needs its entire business logic implemented — from MAVLink communication through flight control, safety monitoring, external solver integration, payload delivery, to full mission integration with CI/CD. This batch change covers Phases 3-8 of the meta development plan, delivering a complete autonomous fixed-wing drone control system ready for SITL validation.

## What Changes

- **Phase 3 — MAVLink Communication Layer**: Full MAVLink adapter (serial/UDP connection, heartbeat watchdog, telemetry parsing to typed dataclasses, async message dispatch via Queue). Includes SITL environment setup for integration testing.
- **Phase 4 — State Machine Engine + Safety Monitor**: Generalized FSM engine with 3 base states (INIT, OVERRIDE, EMERGENCY), global safety monitor coroutine (battery, GPS, heartbeat, airspeed, geofence checks), override detection, and telemetry flight recorder.
- **Phase 5 — Flight Command Layer + Scan/Landing + Business States**: High-level flight commands (arm/takeoff/goto/set_mode), MAVLink Mission Upload Protocol for scan waypoints and landing sequences, and all business states (PREFLIGHT, TAKEOFF, SCAN, LOITER, ENROUTE, LANDING, COMPLETED) with SCAN↔LOITER timeout-rescan loop.
- **Phase 6 — External Solver Link + Coordinate Utilities**: TCP/UDP coordinate receivers, target tracker with adaptive frequency smoothing, coordinate converter, point-in-polygon test, geofence random point generator for forced strike.
- **Phase 7 — Payload System**: Ballistic solver engine with WGS-84 accurate release point calculation, dual-channel release mechanism (MAVLink Servo / GPIO), forced-strike degradation state.
- **Phase 8 — Full Mission Integration + CI/CD**: Main loop orchestration in app.py, CI/CD pipeline (GitHub Actions), complete SITL full-mission tests (normal + degradation paths), deployment scripts, and architecture documentation.

## Capabilities

### New Capabilities
- `comms-mavlink-adapter`: MAVLink connection management, heartbeat monitoring, telemetry parsing, async message dispatch
- `sitl-environment`: ArduPlane SITL setup scripts, integration test fixtures
- `fsm-engine`: Generalized async FSM engine with state lifecycle, event processing, global interceptors
- `safety-monitor`: Continuous safety checks (battery, GPS, heartbeat, airspeed, geofence), override detection, emergency triggering
- `flight-controller`: High-level flight commands, mode management, speed control
- `mission-upload`: MAVLink Mission Upload Protocol for waypoints and landing sequences
- `scan-loiter-states`: SCAN↔LOITER loop with cycle counting, timeout, and rescan logic
- `business-states`: PREFLIGHT, TAKEOFF, ENROUTE, LANDING, COMPLETED state implementations
- `vision-receiver`: External solver coordinate reception via TCP/UDP, VisionReceiver Protocol
- `target-tracker`: Sliding window median filter with adaptive frequency smoothing
- `geo-utilities`: GPS calculations, coordinate conversion (NED↔WGS-84), unit conversions, timing
- `point-in-polygon`: Ray-casting point-in-polygon test for geofence validation
- `forced-strike-point`: Geofence-constrained random point generator with safety buffer exclusion
- `ballistic-solver`: Free-fall parabolic trajectory solver with wind compensation, WGS-84 release point
- `payload-release`: Dual-channel release (MAVLink DO_SET_SERVO + GPIO via gpiod) with ACK verification
- `forced-strike-state`: Forced bombing degradation after max scan cycle timeout
- `flight-recorder`: CSV flight data recording and GCS status reporting interface
- `app-main-loop`: Asyncio main loop orchestration, subsystem initialization, field profile loading
- `ci-cd-pipeline`: GitHub Actions CI with lint, type-check, unit tests, registry checks, SITL integration
- `deployment-scripts`: Preflight check, registry lint, pkg version check, RPi5 setup scripts

### Modified Capabilities
- `config-system`: Add new config fields for comms, safety thresholds, release method, field profile path
- `project-framework`: Add new dependencies (geopy, python-statemachine, gpiod), update pyproject.toml

## Impact

- **New source directories**: `src/striker/comms/`, `src/striker/core/`, `src/striker/flight/`, `src/striker/safety/`, `src/striker/vision/`, `src/striker/payload/`, `src/striker/utils/`
- **New dependencies**: `geopy` (WGS-84 distance), `python-statemachine` (FSM), `gpiod` (GPIO control, optional)
- **Test infrastructure**: Integration test framework with SITL fixtures, ~80+ unit tests, ~10+ integration tests
- **CI/CD**: GitHub Actions workflow with multi-stage pipeline
- **Documentation**: 5+ new documentation files (architecture, config reference, field profile guide, states, ballistics, wiring)
