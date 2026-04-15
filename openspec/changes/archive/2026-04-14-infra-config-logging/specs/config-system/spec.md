## ADDED Requirements

### Requirement: Three-layer configuration priority
The system SHALL implement `StrikerSettings(BaseSettings)` with a three-layer configuration priority: code defaults (lowest) < JSON config file < environment variables (highest). The priority order SHALL be enforced via `settings_customise_sources()`.

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

---

### Requirement: Configuration fields with sensible defaults
The system SHALL define the following configuration fields with code-level defaults: `serial_port` (str), `serial_baud` (int), `loiter_radius_m` (float), `loiter_timeout_s` (float), `max_scan_cycles` (int), `forced_strike_enabled` (bool), `field` (str), `dry_run` (bool), `log_level` (str).

#### Scenario: All fields have default values
- **WHEN** `StrikerSettings()` is instantiated with no config file and no environment variables
- **THEN** all fields return their default values without raising validation errors

#### Scenario: Field name selects field profile
- **WHEN** `STRIKER_FIELD=zijingang` environment variable is set
- **THEN** `StrikerSettings().field` returns `"zijingang"`

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

#### Scenario: Loiter radius must be positive
- **WHEN** `loiter_radius_m` is set to `0` or a negative number
- **THEN** pydantic validation raises `ValidationError`

#### Scenario: Loiter timeout must be positive
- **WHEN** `loiter_timeout_s` is set to `0` or a negative number
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
