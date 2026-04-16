### Requirement: 人工接管必须由飞控模式变化触发自动退让
系统 SHALL 监测飞控模式变化，并在模式切换到人工接管模式集合（如 `MANUAL`、`STABILIZE`、`FBWA` 或经项目确认的等价模式）时立即发出 `OverrideEvent`。

#### Scenario: AUTO 中切入人工模式
- **WHEN** 飞行器当前处于自动任务链路，且飞控模式切换到人工接管模式集合中的任一模式
- **THEN** 系统必须立即发出 `OverrideEvent`

#### Scenario: 非人工模式切换
- **WHEN** 飞控模式在自动模式集合内部切换，例如 `AUTO` 到 `GUIDED`
- **THEN** 系统不得把该变化误判为人工接管

### Requirement: Override 触发后必须终止自动状态推进
系统 MUST 在收到 `OverrideEvent` 后进入 `override` 终态，并且不得自动恢复到任务状态链中的任一业务状态。

#### Scenario: override 终态保持
- **WHEN** 状态机已因人工接管进入 `override`
- **THEN** 系统不得自行跳回 `scan`、`enroute`、`release`、`landing` 或其他自动状态

#### Scenario: override 日志与可观测性
- **WHEN** 系统进入 `override`
- **THEN** 系统必须记录是哪个飞控模式变化触发了人工接管退让

### Requirement: 模式解析必须提供可用于接管判定的语义化模式名
系统 SHALL 将飞控模式信息暴露为可直接判定的 ArduPlane 模式名（如 `"MANUAL"`、`"AUTO"`、`"GUIDED"`、`"FBWA"`），而不是仅保留 `custom_mode` 的数字字符串表示。

**实现约束**：pymavlink 的 `mavfile` 连接对象已经提供了 `.flightmode` 属性，会自动将 `custom_mode` 映射为 ArduPlane 模式名（参见 `src/striker/comms/telemetry.py:156` 的注释）。实现时应从连接对象读取 `.flightmode` 而非自行解析原始 `custom_mode` 字段。

#### Scenario: HEARTBEAT 被解析
- **WHEN** 通信层收到 HEARTBEAT 并更新系统状态
- **THEN** 上层安全逻辑必须能够读取语义化模式名（如 `"MANUAL"`、`"AUTO"`、`"GUIDED"`）用于 override 判定，而非原始数字字符串
