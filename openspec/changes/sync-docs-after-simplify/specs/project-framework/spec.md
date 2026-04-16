## MODIFIED Requirements

### Requirement: StrikerSettings contains expected configuration keys
The system SHALL define `StrikerSettings` that contains keys for: `serial_port`, `serial_baud`, `transport`, `mavlink_url`, `battery_min_v`, `stall_speed_mps`, `heartbeat_timeout_s`, `safety_check_interval_s`, `field`, `dry_run`, `release_method`, `release_channel`, `release_pwm_open`, `release_pwm_close`, `release_gpio_pin`, `release_gpio_active_high`, `vision_receiver_type`, `vision_host`, `vision_port`, `recorder_output_path`, `recorder_sample_rate_hz`, `log_level`.

#### Scenario: Settings JSON does not contain removed fields
- **WHEN** `StrikerSettings` is instantiated from a config.json
- **THEN** it SHALL NOT contain keys for `loiter_radius_m`, `loiter_timeout_s`, `max_scan_cycles`, or `forced_strike_enabled`
