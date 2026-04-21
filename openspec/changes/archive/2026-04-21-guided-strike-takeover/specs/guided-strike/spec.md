## ADDED Requirements

### Requirement: GUIDED 模式三阶段打击导航
GuidedStrikeState SHALL 在 on_enter 时读取投弹点（vision 全局变量优先，field profile fallback 降级），计算 approach / target / exit 三个坐标，切换飞控至 GUIDED 模式，并通过 DO_REPOSITION 导航至 approach 点。execute 循环 SHALL 按 APPROACH → STRIKE → EXIT 三阶段执行，每个阶段持续发送 `resend_position_target` keepalive。

#### Scenario: 视觉投弹点可用
- **WHEN** `get_vision_drop_point()` 返回有效坐标
- **THEN** GuidedStrikeState SHALL 使用该坐标作为 target，计算 approach 和 exit 点，切换 GUIDED 并导航

#### Scenario: 视觉投弹点不可用，使用降级点
- **WHEN** `get_vision_drop_point()` 返回 None 且 `field_profile.attack_run.fallback_drop_point` 存在
- **THEN** GuidedStrikeState SHALL 使用 fallback 坐标，标注 source 为 "fallback_field"

#### Scenario: 两者均不可用
- **WHEN** 视觉和 fallback 均不可用
- **THEN** GuidedStrikeState SHALL 记录错误日志，不执行模式切换，保持当前状态

### Requirement: 距离判定到达
GuidedStrikeState SHALL 在每个 phase 中通过 haversine 距离计算判定是否到达目标点。APPROACH 和 EXIT 阶段使用 `wp_radius` 阈值，STRIKE 阶段使用 `release_radius` 阈值（可配置，默认与 wp_radius 相同）。

#### Scenario: APPROACH 阶段到达
- **WHEN** 当前位置与 approach 点的 haversine 距离小于 wp_radius
- **THEN** SHALL 切换内部 phase 为 STRIKE，DO_REPOSITION 目标更新为 target 点

#### Scenario: STRIKE 阶段到达投弹点
- **WHEN** 当前位置与 target 点的 haversine 距离小于 release_radius
- **THEN** SHALL 触发投弹（见投弹触发需求），切换 phase 为 EXIT

#### Scenario: EXIT 阶段到达
- **WHEN** 当前位置与 exit 点的 haversine 距离小于 wp_radius
- **THEN** SHALL 返回 `Transition("release_monitor", ...)`

### Requirement: 程序化投弹触发
GuidedStrikeState SHALL 在 STRIKE 阶段距离判定通过后，通过 `send_command(MAV_CMD_DO_SET_SERVO, param1=channel, param2=pwm)` 主动发送投弹命令，并调用 `context.mark_release_triggered()`。dry_run 模式下 SHALL 跳过 servo 命令但仍标记 release。

#### Scenario: 正常投弹
- **WHEN** STRIKE 阶段距离判定通过且 `dry_run=False`
- **THEN** SHALL 发送 `MAV_CMD_DO_SET_SERVO`，记录 release timestamp

#### Scenario: dry_run 投弹
- **WHEN** STRIKE 阶段距离判定通过且 `dry_run=True`
- **THEN** SHALL 跳过 servo 命令，但 SHALL 调用 `mark_release_triggered()` 并记录日志

### Requirement: GUIDED keepalive
GuidedStrikeState SHALL 在每个 execute 循环（50ms）中调用 `resend_position_target()` 发送当前阶段的目标坐标，确保飞控持续收到导航指令。

#### Scenario: 目标位置持续发送
- **WHEN** GuidedStrikeState 处于任意 phase
- **THEN** 每次 execute 调用 SHALL 发送一次 `resend_position_target` 到当前 phase 的目标坐标
