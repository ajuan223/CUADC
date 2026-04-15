## MODIFIED Requirements

### Requirement: Three-layer configuration priority
The system SHALL implement `StrikerSettings(BaseSettings)` with a three-layer configuration priority: code defaults (lowest) < JSON config file < environment variables (highest). The priority order SHALL be enforced via `settings_customise_sources()` returning `(init_settings, JsonConfigSettingsSource(settings_cls), env_settings, file_secret_settings)` so that later sources override earlier ones.

#### Scenario: Code default is used when no override exists
- **WHEN** `StrikerSettings()` is instantiated without a config file or environment variables
- **THEN** each field returns its code-defined default value (e.g., `serial_port` = `"/dev/serial0"`, `serial_baud` = `921600`)

#### Scenario: JSON config overrides code defaults
- **WHEN** a `config.json` file exists with `"serial_port": "/dev/ttyUSB0"`
- **THEN** `StrikerSettings().serial_port` returns `"/dev/ttyUSB0"`

#### Scenario: Environment variable overrides JSON config
- **WHEN** a `config.json` file sets `"serial_port": "/dev/ttyUSB0"` AND environment variable `STRIKER_SERIAL_PORT="/dev/ttyACM0"` is set
- **THEN** `StrikerSettings().serial_port` returns `"/dev/ttyACM0"`

#### Scenario: Environment variable prefix is STRIKER_
- **WHEN** environment variable `STRIKER_DRY_RUN=true` is set
- **THEN** `StrikerSettings().dry_run` returns `True`

#### Scenario: JSON overrides defaults but not env vars
- **WHEN** `settings_customise_sources` returns the tuple
- **THEN** the order is `(init_settings, JsonConfigSettingsSource, env_settings, file_secret_settings)` — env vars have highest priority

## ADDED Requirements

### Requirement: HeartbeatMonitor accepts MAVLinkConnection type
`HeartbeatMonitor` constructor SHALL accept a `MAVLinkConnection` instance as its `conn` parameter (not `mavutil.mavfile`). It SHALL use `conn.send()` for sending heartbeat messages and `conn.mav` for accessing target system/component IDs only when constructing messages.

#### Scenario: HeartbeatMonitor constructs with MAVLinkConnection
- **WHEN** `HeartbeatMonitor(conn=MAVLinkConnection_instance)` is constructed
- **THEN** the type checker accepts the parameter and no runtime error occurs

#### Scenario: HeartbeatMonitor sends heartbeat via connection
- **WHEN** `HeartbeatMonitor._heartbeat_sender()` executes
- **THEN** it calls `self._conn.send(heartbeat_message)` where heartbeat_message is built from comms-layer constants

### Requirement: gpiod is an optional dependency
The system SHALL declare `gpiod` as an optional dependency in `pyproject.toml` under `[project.optional-dependencies]` with group name `gpio`. The core system SHALL install and run without `gpiod` present.

#### Scenario: Core install without gpio extras
- **WHEN** `uv sync` is run (without `--extra gpio`)
- **THEN** the installation succeeds and `import striker` works without `gpiod`

#### Scenario: GPIO extras install includes gpiod
- **WHEN** `uv sync --extra gpio` is run
- **THEN** `gpiod` is available for import

### Requirement: app.py starts vision receiver before task group
`app.py` SHALL call `await vision_receiver.start()` before entering the `asyncio.TaskGroup` block. A `_vision_dispatch()` coroutine SHALL run in the TaskGroup, periodically polling `vision_receiver.get_latest()` and pushing new targets to `target_tracker.push()`.

#### Scenario: Vision receiver is started on app launch
- **WHEN** `app.py` main() executes
- **THEN** `vision_receiver.start()` is awaited before the TaskGroup is created

#### Scenario: Vision dispatch pushes targets to tracker
- **WHEN** the vision receiver receives a new GpsTarget
- **THEN** within 100ms the `_vision_dispatch` coroutine pushes it to `target_tracker.push(lat, lon)`

### Requirement: SafetyMonitor event callback is connected to FSM
`app.py` SHALL call `safety_monitor.set_event_callback()` with a callback that forwards `EmergencyEvent` and `OverrideEvent` to `fsm.process_event()`.

#### Scenario: Safety check failure triggers FSM emergency
- **WHEN** the battery voltage drops below threshold
- **THEN** the SafetyMonitor emits an EmergencyEvent which reaches `fsm.process_event()` and the FSM transitions to EMERGENCY state

#### Scenario: Override detection triggers FSM override
- **WHEN** the flight controller mode changes to MANUAL
- **THEN** the SafetyMonitor emits an OverrideEvent which reaches `fsm.process_event()` and the FSM transitions to OVERRIDE state

### Requirement: FSM transitions include forced_strike as source state
The `MissionStateMachine` SHALL declare transitions where `forced_strike` is a valid source state: `forced_strike.to(landing)`, `forced_strike.to(override)`, and `forced_strike.to(emergency)`.

#### Scenario: Forced strike transitions to landing after release
- **WHEN** `ForcedStrikeState.execute()` returns `Transition(target_state="landing")`
- **THEN** the FSM successfully transitions to LANDING state without raising `TransitionNotAllowed`

#### Scenario: Global interceptor works from forced_strike
- **WHEN** `fsm.process_event(OverrideEvent())` is called while in FORCED_STRIKE state
- **THEN** the FSM transitions to OVERRIDE state

#### Scenario: Emergency interceptor works from forced_strike
- **WHEN** `fsm.process_event(EmergencyEvent())` is called while in FORCED_STRIKE state
- **THEN** the FSM transitions to EMERGENCY state
