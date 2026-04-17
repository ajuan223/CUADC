## MODIFIED Requirements

### Requirement: Configuration fields with sensible defaults
The system SHALL define the following configuration fields with code-level defaults: `serial_port` (str), `serial_baud` (int), `transport` (str), `mavlink_url` (str), `battery_min_v` (float), `stall_speed_mps` (float), `heartbeat_timeout_s` (float), `safety_check_interval_s` (float), `field` (str), `dry_run` (bool), `arm_force_bypass` (bool, default `False`), `release_method` (str), `release_channel` (int), `release_pwm_open` (int), `release_pwm_close` (int), `release_gpio_pin` (int), `release_gpio_active_high` (bool), `vision_receiver_type` (str), `vision_host` (str), `vision_port` (int), `recorder_output_path` (str), `recorder_sample_rate_hz` (float), and `log_level` (str). The standard configuration interface MUST NOT expose `loiter_radius_m`, `loiter_timeout_s`, `max_scan_cycles`, or `forced_strike_enabled` as active settings.

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
