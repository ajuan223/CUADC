## ADDED Requirements

### Requirement: LandingMonitorState 执行 GUIDED→AUTO 模式切换
LandingMonitorState.on_enter() SHALL 执行 `MISSION_SET_CURRENT(landing_start_seq)` 后 `set_mode(AUTO)`，将飞控从 GUIDED 模式切回 AUTO 执行预烧录降落段。

#### Scenario: 正常切换降落
- **WHEN** 从 release_monitor 转换进入 landing_monitor
- **THEN** on_enter SHALL 先发送 MISSION_SET_CURRENT 到 landing_start_seq，再切 AUTO 模式

#### Scenario: 降落段执行
- **WHEN** AUTO 模式激活且 mission current 设置为 landing_start_seq
- **THEN** 飞控 SHALL 自动执行 DO_LAND_START 降落序列
