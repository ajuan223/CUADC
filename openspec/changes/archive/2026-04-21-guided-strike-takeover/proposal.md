## Why

当前打击流程依赖预烧录任务中 5 个空白 mission slot，通过 `partial_write_mission()` 在飞行中覆写注入攻击航点，全程保持 Auto 模式。此方案存在三个核心问题：
1. **协议脆弱性** — `partial_write_mission` 依赖飞控逐条 ACK 应答，超时或丢包直接导致注入失败
2. **精度受限** — 投弹点一次写死为 mission item，飞控按 `WP_RADIUS` 粗粒度判定到达，无法修正
3. **配置耦合** — Mission Planner 预烧录任务必须精确预留 5 个空白 slot，结构脆弱

新策略：scan 预烧录航点结束后，取消空白 slot，直接切换 GUIDED 模式由程序完全接管导航和投弹。

## What Changes

- **新增** `guided_strike` 状态，替代 `loiter_hold` + `attack_run` 两个状态
- **BREAKING** 预烧录任务结构变更：LOITER_UNLIM 后直接 DO_LAND_START，删除 5 个空白 slot
- `PreburnedMissionInfo` 删除 `slot_start_seq` / `slot_end_seq` 字段
- 投弹从飞控自动执行 `DO_SET_SERVO` mission item 改为程序主动发送 `DO_SET_SERVO` MAVLink 命令
- `landing_monitor` 新增 GUIDED→AUTO 模式切换 + `MISSION_SET_CURRENT` 跳转降落段
- `attack_geometry.py` 简化为纯几何计算，不再生成 mission items
- FSM 状态链调整：删除 `loiter_hold` / `attack_run` 声明，新增 `guided_strike`

## Capabilities

### New Capabilities
- `guided-strike`: GUIDED 模式下的程序化打击状态，包含 approach→strike→exit 三阶段导航、距离判定投弹触发、GUIDED keepalive

### Modified Capabilities
- `scan-loiter-states`: scan_monitor 触发条件不变（仍监听 loiter_seq），但后续状态从 loiter_hold 改为 guided_strike
- `flight-controller`: 新增 GUIDED 模式导航在打击流程中的正式使用（goto / resend_position_target 已存在）
- `mission-upload`: `partial_write_mission` 不再是主流程必需，保留但降级为可选工具
- `fsm-engine`: 状态声明和转换链变更
- `business-states`: 状态注册表更新
- `attack-run`: 被 guided-strike 替代，标记废弃
- `simplified-mission-flow`: 预烧录任务结构变更，删除 slot 概念

## Impact

- **预烧录任务**: Mission Planner 中所有场地的预烧录任务需重新配置（删除 5 个空白 slot）
- **field profile**: `attack_run` 配置不变（approach_distance_m、exit_distance_m 复用）
- **SITL 测试**: 预烧录任务文件需同步更新
- **safety monitor**: 无影响（GUIDED 已在 `_autonomous_modes` 集合中）
- **代码文件**: `loiter_hold.py`、`attack_run.py` 删除；新增 `guided_strike.py`；修改 `machine.py`、`preburned_mission.py`、`scan_monitor.py`、`release_monitor.py`、`landing_monitor.py`、`attack_geometry.py`、`app.py`、`states/__init__.py`
