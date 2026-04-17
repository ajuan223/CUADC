## ADDED Requirements

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

---

### Requirement: Configuration fields with sensible defaults
The system SHALL define the following configuration fields with code-level defaults: `serial_port` (str), `serial_baud` (int), `transport` (str), `mavlink_url` (str), `battery_min_v` (float), `stall_speed_mps` (float), `heartbeat_timeout_s` (float), `safety_check_interval_s` (float), `field` (str), `dry_run` (bool), `arm_force_bypass` (bool, default `False`), `release_method` (str), `release_channel` (int), `release_pwm_open` (int), `release_pwm_close` (int), `release_gpio_pin` (int), `release_gpio_active_high` (bool), `vision_receiver_type` (str), `vision_host` (str), `vision_port` (int), `recorder_output_path` (str), `recorder_sample_rate_hz` (float), `log_level` (str). The standard configuration interface MUST NOT expose `loiter_radius_m`, `loiter_timeout_s`, `max_scan_cycles`, or `forced_strike_enabled` as active settings.

#### Scenario: All fields have default values
- **WHEN** `StrikerSettings()` is instantiated with no config file and no environment variables
- **THEN** all fields return their default values without raising validation errors, and `arm_force_bypass` returns `False`

#### Scenario: Field name selects field profile
- **WHEN** `STRIKER_FIELD=zijingang` environment variable is set
- **THEN** `StrikerSettings().field` returns `"zijingang"`

#### Scenario: SITL enables arm force bypass via environment variable
- **WHEN** environment variable `STRIKER_ARM_FORCE_BYPASS=true` is set
- **THEN** `StrikerSettings().arm_force_bypass` returns `True`

#### Scenario: Arm force bypass defaults to False for real deployment
- **WHEN** no override exists for `arm_force_bypass`
- **THEN** `StrikerSettings().arm_force_bypass` returns `False` and arming requires passing all pre-arm checks

#### Scenario: Public config examples omit deprecated mission settings
- **WHEN** operators consult `config.example.json` or `.env.example`
- **THEN** the examples MUST omit `loiter_radius_m`, `loiter_timeout_s`, `max_scan_cycles`, and `forced_strike_enabled`

---

### Requirement: JSON config file path is configurable
The system SHALL load JSON configuration from `config.json` in the working directory by default. The file path SHALL be specified via `SettingsConfigDict.json_file`.

#### Scenario: Config file does not exist
- **WHEN** `config.json` does not exist in the working directory
- **THEN** `StrikerSettings()` instantiates successfully using code defaults

#### Scenario: Config file contains invalid JSON
- **WHEN** `config.json` contains malformed JSON
- **THEN** instantiating `StrikerSettings` raises a validation error

---

### Requirement: Physical quantity validators
The system SHALL validate that physical quantity fields fall within sensible ranges using pydantic validators.

#### Scenario: Baud rate must be positive
- **WHEN** `serial_baud` is set to `0` or a negative number
- **THEN** pydantic validation raises `ValidationError`

---

### Requirement: Platform detection
The system SHALL provide `detect_platform()` that returns a `Platform` enum value: `RPi5`, `Orin`, `SITL`, or `Unknown`.

#### Scenario: Detect SITL via environment variable
- **WHEN** environment variable `MAVLINK_SITL` is set (to any value)
- **THEN** `detect_platform()` returns `Platform.SITL`

#### Scenario: Detect Raspberry Pi 5
- **WHEN** `/proc/device-tree/model` exists and contains `"Raspberry Pi 5"`
- **THEN** `detect_platform()` returns `Platform.RPi5`

#### Scenario: Detect NVIDIA Orin
- **WHEN** `/etc/nv_tegra_release` exists
- **THEN** `detect_platform()` returns `Platform.Orin`

#### Scenario: Unknown platform fallback
- **WHEN** none of the detection conditions match
- **THEN** `detect_platform()` returns `Platform.Unknown`

#### Scenario: Manual platform override via environment variable
- **WHEN** environment variable `STRIKER_PLATFORM` is set to `"sitl"`
- **THEN** `detect_platform()` returns `Platform.SITL` regardless of filesystem state

---

### Requirement: HeartbeatMonitor accepts MAVLinkConnection type
`HeartbeatMonitor` constructor SHALL accept a `MAVLinkConnection` instance as its `conn` parameter (not `mavutil.mavfile`). It SHALL use `conn.send()` for sending heartbeat messages and `conn.mav` for accessing target system/component IDs only when constructing messages.

#### Scenario: HeartbeatMonitor constructs with MAVLinkConnection
- **WHEN** `HeartbeatMonitor(conn=MAVLinkConnection_instance)` is constructed
- **THEN** the type checker accepts the parameter and no runtime error occurs

#### Scenario: HeartbeatMonitor sends heartbeat via connection
- **WHEN** `HeartbeatMonitor._heartbeat_sender()` executes
- **THEN** it calls `self._conn.send(heartbeat_message)` where heartbeat_message is built from comms-layer constants

---

### Requirement: gpiod is an optional dependency
The system SHALL declare `gpiod` as an optional dependency in `pyproject.toml` under `[project.optional-dependencies]` with group name `gpio`. The core system SHALL install and run without `gpiod` present.

#### Scenario: Core install without gpio extras
- **WHEN** `uv sync` is run (without `--extra gpio`)
- **THEN** the installation succeeds and `import striker` works without `gpiod`

#### Scenario: GPIO extras install includes gpiod
- **WHEN** `uv sync --extra gpio` is run
- **THEN** `gpiod` is available for import

---

### Requirement: app.py starts vision receiver before task group
`app.py` SHALL call `await vision_receiver.start()` before entering the `asyncio.TaskGroup` block. A `_vision_dispatch()` coroutine SHALL run in the TaskGroup, periodically polling `vision_receiver.get_latest()` and pushing new drop points to `drop_point_tracker.push()`.

#### Scenario: Vision receiver is started on app launch
- **WHEN** `app.py` main() executes
- **THEN** `vision_receiver.start()` is awaited before the TaskGroup is created

#### Scenario: Vision dispatch pushes drop points to tracker
- **WHEN** the vision receiver receives a new `GpsDropPoint`
- **THEN** within 100ms the `_vision_dispatch` coroutine pushes it to `drop_point_tracker.push(lat, lon)`

---

### Requirement: SafetyMonitor event callback is connected to FSM
`app.py` SHALL call `safety_monitor.set_event_callback()` with a callback that forwards `EmergencyEvent` and `OverrideEvent` to `fsm.process_event()`.

#### Scenario: Safety check failure triggers FSM emergency
- **WHEN** the battery voltage drops below threshold
- **THEN** the SafetyMonitor emits an EmergencyEvent which reaches `fsm.process_event()` and the FSM transitions to EMERGENCY state

#### Scenario: Override detection triggers FSM override
- **WHEN** the flight controller mode changes to MANUAL
- **THEN** the SafetyMonitor emits an OverrideEvent which reaches `fsm.process_event()` and the FSM transitions to OVERRIDE state
