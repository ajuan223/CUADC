## REMOVED Requirements

### Requirement: Loiter / scan cycle configuration fields
**Reason**: `simplify-mission-flow-drop-point` 变更已删除 loiter/forced_strike 主流程，相关配置字段 `loiter_radius_m`、`loiter_timeout_s`、`max_scan_cycles`、`forced_strike_enabled` 已从 `StrikerSettings` 中移除。
**Migration**: 不再需要这些配置，删除即可。

### Requirement: FSM transitions include forced_strike as source state
**Reason**: `forced_strike` 状态已从状态机中删除。
**Migration**: 状态机不再包含 forced_strike 状态。

## MODIFIED Requirements

### Requirement: App vision dispatch uses drop point tracker
`app.py` SHALL call `await vision_receiver.start()` before entering the `asyncio.TaskGroup` block. A `_vision_dispatch()` coroutine SHALL run in the TaskGroup, periodically polling `vision_receiver.get_latest()` and pushing new drop points to `drop_point_tracker.push()`.

#### Scenario: Vision receiver pushes drop point to tracker
- **WHEN** the vision receiver receives a new `GpsDropPoint`
- **THEN** within 100ms the `_vision_dispatch` coroutine pushes it to `drop_point_tracker.push(lat, lon)`

### Requirement: StrikerSettings defines core configuration fields
The system SHALL define the following configuration fields with code-level defaults: `serial_port` (str), `serial_baud` (int), `battery_min_v` (float), `stall_speed_mps` (float), `heartbeat_timeout_s` (float), `safety_check_interval_s` (float), `field` (str), `dry_run` (bool), `release_method` (str), `release_channel` (int), `release_pwm_open` (int), `release_pwm_close` (int), `release_gpio_pin` (int), `release_gpio_active_high` (bool), `vision_receiver_type` (str), `vision_host` (str), `vision_port` (int), `recorder_output_path` (str), `recorder_sample_rate_hz` (float), `log_level` (str).

#### Scenario: Config JSON contains only current fields
- **WHEN** a valid `config.json` is loaded
- **THEN** it SHALL NOT contain keys for `loiter_radius_m`, `loiter_timeout_s`, `max_scan_cycles`, or `forced_strike_enabled`

### Requirement: Serial baud rate validator
The system SHALL validate that `serial_baud` is a positive integer.

#### Scenario: Zero baud rejected
- **WHEN** `serial_baud` is set to `0`
- **THEN** pydantic validation SHALL raise `ValidationError`

#### Scenario: Negative baud rejected
- **WHEN** `serial_baud` is set to `-1`
- **THEN** pydantic validation SHALL raise `ValidationError`
