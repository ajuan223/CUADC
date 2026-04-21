## Context

当前 Striker 任务系统采用"预烧录旁路注入"模式：飞控预烧录完整任务含 5 个空白 slot，Striker 在 `loiter_hold` 状态通过 `partial_write_mission()` 覆写 slot 注入攻击航点，全程 Auto 模式。

关键现状：
- `FlightController` 已具备完整 GUIDED 基础设施（`goto`、`resend_position_target`、`set_mode`）
- `vision/global_var.py` 中 `VISION_DROP_POINT` 在 scan 结束时一次性写入
- `field_profile.attack_run.fallback_drop_point` 提供降级投弹点
- LOITER_UNLIM 仅作最终安全锚（Striker 进程崩溃时飞机不坠毁）

## Goals / Non-Goals

**Goals:**
- 消除 5 个空白 slot 和 `partial_write_mission` 协议在主流程中的依赖
- 用 GUIDED 模式 DO_REPOSITION 实现程序化打击导航（approach→strike→exit）
- 程序主动发送 DO_SET_SERVO 实现精确投弹触发
- 投弹完成后安全切回 AUTO 模式执行预烧录降落段
- 保留 LOITER_UNLIM 作为进程崩溃兜底

**Non-Goals:**
- 不改动视觉系统接口（投弹点仍为一次性全局变量）
- 不改动 field profile 数据模型（approach_distance_m / exit_distance_m 复用）
- 不改动安全监控系统
- 不实现实时跟踪移动目标（投弹点一次性确定后不变）
- 不删除 `partial_write_mission` 代码（保留为可选工具）

## Decisions

### D1: 用单状态内部三阶段替代双状态

**选择**: 新增 `GuidedStrikeState` 替代 `LoiterHoldState` + `AttackRunState`

**替代方案**: 保留双状态（`guided_approach` + `guided_strike`）

**理由**: 三阶段（APPROACH / STRIKE / EXIT）共享同一套 GUIDED 导航逻辑和投弹点数据，拆成两个状态会引入额外的状态转换和 context 数据传递。内部 phase 枚举更简洁。

### D2: 保留 LOITER_UNLIM 作为安全锚

**选择**: 预烧录任务保留 `NAV_LOITER_UNLIM`，但 LOITER 后不再有空白 slot

**替代方案**: 完全移除 LOITER，scan 最后 WP 后直接 DO_LAND_START

**理由**: LOITER 是 Striker 进程崩溃时的最终兜底——飞机不会飞向虚空。正常流程中 Striker 到达 loiter_seq 后立即切 GUIDED，不会实际盘旋等待。成本为零、安全收益为正。

### D3: 程序化 DO_SET_SERVO 投弹

**选择**: `GuidedStrikeState` 在 STRIKE 阶段距离判定通过后，通过 `send_command(MAV_CMD_DO_SET_SERVO)` 主动投弹

**替代方案**: 保留 mission item 中的 DO_SET_SERVO（需要在 GUIDED 中临时切 AUTO 执行一条 mission item）

**理由**: GUIDED 模式下飞控不执行 mission items。程序化发送 DO_SET_SERVO 是唯一直接的方式，且精度完全由 Striker 距离判定决定，不受 WP_RADIUS 限制。

### D4: 距离判定使用 haversine

**选择**: 在 `utils/geo.py` 中新增 `haversine_distance()` 用于 GUIDED 阶段的到达判定

**替代方案**: 复用飞控的 WP_RADIUS 并通过 MISSION_ITEM_REACHED 判定

**理由**: GUIDED 模式下不存在 mission item，没有 MISSION_ITEM_REACHED 消息。必须程序自行计算距离。haversine 在短距离（<1km）精度足够。

### D5: landing_monitor 负责 GUIDED→AUTO 切换

**选择**: `LandingMonitorState.on_enter()` 中执行 `MISSION_SET_CURRENT(landing_start_seq)` + `set_mode(AUTO)`

**替代方案**: 在 `GuidedStrikeState` EXIT 阶段完成后切 AUTO，再转 landing_monitor

**理由**: 模式切换和 mission 跳转是降落段的前置条件，放在 landing_monitor 的 on_enter 最内聚。

## Risks / Trade-offs

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| DO_REPOSITION 命令丢失导致飞机飞向旧目标 | 中 | `resend_position_target()` 每 50ms 循环发送 keepalive |
| haversine 距离判定精度不足 | 低 | 短距离（<500m）误差 <0.1%，远超 WP_RADIUS 需求 |
| GUIDED→AUTO 切换期间飞控行为不确定 | 中 | 先 `MISSION_SET_CURRENT` 设置好目标 seq，再 `set_mode(AUTO)`，顺序确定 |
| Striker 在 GUIDED 阶段崩溃 | 中 | ArduPlane GCS failsafe → RTL；LOITER 安全锚兜底 |
| dry_run 模式下 DO_SET_SERVO 不应发送 | 低 | STRIKE 阶段检查 `context.settings.dry_run`，跳过 servo 命令 |
