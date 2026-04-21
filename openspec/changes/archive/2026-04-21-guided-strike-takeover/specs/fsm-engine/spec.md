## MODIFIED Requirements

### Requirement: MissionStateMachine shall register states in a dict with string keys
状态机 SHALL 注册以下状态（含新增 guided_strike，移除 loiter_hold 和 attack_run）：init, standby, scan_monitor, guided_strike, release_monitor, landing_monitor, completed, override, emergency。

#### Scenario: 状态声明
- **WHEN** MissionStateMachine 初始化
- **THEN** SHALL 声明 `guided_strike` State，不再声明 `loiter_hold` 和 `attack_run`

#### Scenario: 转换声明
- **WHEN** 定义状态转换
- **THEN** SHALL 包含 `scan_monitor.to(guided_strike)` 和 `guided_strike.to(release_monitor)` 转换；SHALL 移除 `scan_monitor.to(loiter_hold)`、`loiter_hold.to(attack_run)`、`attack_run.to(release_monitor)` 转换

#### Scenario: override 和 emergency 覆盖
- **WHEN** 定义 to_override 和 to_emergency 转换
- **THEN** SHALL 包含从 `guided_strike` 到 override/emergency 的转换路径
