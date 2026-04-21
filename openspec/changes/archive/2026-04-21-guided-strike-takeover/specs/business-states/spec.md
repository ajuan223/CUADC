## MODIFIED Requirements

### Requirement: Business states shall implement the latest preburned mission flow (standby, scan_monitor, guided_strike, release_monitor, landing_monitor)
业务状态 SHALL 实现最新预烧录任务流：`standby → scan_monitor → guided_strike → release_monitor → landing_monitor → completed`。`loiter_hold` 和 `attack_run` 状态 SHALL 被移除，由 `guided_strike` 替代。

#### Scenario: 状态注册表
- **WHEN** 系统初始化状态机
- **THEN** SHALL 注册 `guided_strike` 状态实例，不再注册 `loiter_hold` 和 `attack_run`

#### Scenario: 状态转换链
- **WHEN** scan_monitor 完成
- **THEN** SHALL 转换到 `guided_strike`（非 `loiter_hold`）
