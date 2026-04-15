## Context

Phase 3-8 代码已按 batch change 生成了完整的模块骨架，但系统性审查发现 13 处偏离设计文档的缺陷。这些缺陷分为三类：运行时必崩的阻塞性问题 (F-01/02/03)、核心约束违反与逻辑错误 (F-04~08)、设计不一致与缺失产出物 (F-09~13)。

当前代码已通过 `uv sync` 和静态检查但无法正确运行完整任务流程。本次修改不引入新模块，仅修正已有代码使其符合设计文档。

## Goals / Non-Goals

**Goals:**
- 修复 3 个 P0 阻塞性缺陷，使 FSM 降级路径、视觉接收、安全监控正常运行
- 修复 RL-04 pymavlink 隔离约束，将 pymavlink 常量收敛到 comms 层
- 修正配置优先级顺序为 `init < json < env`
- 修正 LandingState 使用 DO_LAND_START 降落序列
- 补全 Phase 0 缺失产出物（py.typed, .env.example, field.json, pkg/）
- 增强 forced_strike_point 安全缓冲区排除逻辑
- 统一距离计算使用 haversine_distance

**Non-Goals:**
- 不修改 FSM 架构（继续使用 python-statemachine 声明式 + 命令式混合模式）
- 不新增业务功能或新状态
- 不重构 HeartbeatMonitor 为独立于 MAVLinkConnection 的设计（仅修正类型标注）
- 不修改 Mission Upload Protocol 的实现

## Decisions

### D1: pymavlink 常量收敛策略 — 纯整数常量导出

**选择**: 在 `comms/messages.py` 中定义 MAVLink 命令 ID 和标志位为模块级整数常量（如 `MAV_CMD_ARM_DISARM = 400`），flight/ 和 payload/ 引用这些常量。

**替代方案 A**: 在 comms/ 提供封装函数（如 `arm(conn)`, `set_mode(conn, mode_id)`）。——过度封装，flight/controller.py 已有高层封装。
**替代方案 B**: 在 comms/ 导出 `from pymavlink.mavlink import *` 的子集。——仍然是间接导入 pymavlink，且暴露面大。

**理由**: 常量是最小侵入的修复方式。MAVLink 命令 ID 是协议规范中的固定整数，提取后无需依赖 pymavlink 即可使用。

需要导出的常量列表:
- `MAV_CMD_COMPONENT_ARM_DISARM = 400`
- `MAV_CMD_NAV_TAKEOFF = 22`
- `MAV_CMD_DO_SET_MODE = 176`
- `MAV_CMD_DO_CHANGE_SPEED = 178`
- `MAV_CMD_DO_SET_SERVO = 183`
- `MAV_CMD_DO_LAND_START = 189`
- `MAV_CMD_NAV_LAND = 21`
- `MAV_CMD_NAV_WAYPOINT = 16`
- `MAV_MODE_FLAG_CUSTOM_MODE_ENABLED = 1`
- `MAV_MODE_FLAG_SAFETY_ARMED = 128`
- `MAV_RESULT_ACCEPTED = 0`
- `MAV_TYPE_GCS = 6`
- `MAV_AUTOPILOT_INVALID = 8`
- `MAV_FRAME_GLOBAL_RELATIVE_ALT = 3`
- `MAV_FRAME_GLOBAL_RELATIVE_ALT_INT = 6`

### D2: FSM 转换表修复 — 补充 forced_strike 源状态

**选择**: 在 `machine.py` 中将 `forced_strike` 添加为以下转换的源状态:
- `to_landing |= forced_strike.to(landing)`
- `to_override |= forced_strike.to(override)`
- `to_emergency |= forced_strike.to(emergency)`

**理由**: forced_strike 是降级路径的关键状态，必须能转到 landing（投弹完成）、override（人工接管）和 emergency（安全违规）。

### D3: app.py 修复 — vision + safety 集成

**选择**:
1. 在 TaskGroup 中添加 `tg.create_task(vision_receiver.start())` — 但需改为长期运行的协程（当前 start() 不是协程循环）。方案：包装为 `vision_receiver_loop()` 或直接在 TaskGroup 外先 `await vision_receiver.start()`，然后依靠 `_rx_loop` 中已有的 vision 数据推送。
2. 在 `SafetyMonitor.set_event_callback()` 中注册 lambda 将事件转发到 `fsm.process_event()`。

**决策**: vision_receiver.start() 是一次性启动（创建 TCP server），不是循环协程。正确的做法是在 TaskGroup 创建前调用 `await vision_receiver.start()`，然后在 TaskGroup 中添加一个消息分发协程从 vision_receiver 轮询最新目标并推送到 tracker。但由于 TcpReceiver 已经是 asyncio server（通过 _handle_connection 自动接收数据），只需要 start() 后定期检查 get_latest() 即可。

最终方案: app.py 中在 TaskGroup 前调用 `await vision_receiver.start()`，添加一个 `_vision_dispatch()` 协程在 TaskGroup 中运行，定期调用 `vision_receiver.get_latest()` 推送到 `target_tracker.push()`。

### D4: 配置优先级修正

**选择**: 调整 `settings_customise_sources` 返回顺序为:
```python
return (init_settings, JsonConfigSettingsSource(settings_cls), env_settings, file_secret_settings)
```

pydantic-settings 源码确认：元组中**后出现**的源优先级更高。修改后优先级: init < json < env，符合设计文档。

### D5: LandingState 降落序列

**选择**: LandingState 改为:
1. 通过 `conn.mav.mav.set_message_interval()` 设置 MISSION_CURRENT 频率
2. 设置 AUTO 模式（如果当前不在 AUTO）
3. 发送 `MAV_CMD_DO_GO_AROUND` 或直接设置当前航点为降落序列起始索引
4. 等待 NAV_LAND 完成（高度接近 0 + 低速度）

简化方案（当前阶段）: 设置 AUTO 模式 + 发送 `MAV_CMD_MISSION_SET_CURRENT` 跳转到降落序列起始航点。

### D6: HeartbeatMonitor 类型修正

**选择**: 将 `conn` 参数类型改为 `MAVLinkConnection`，`_heartbeat_sender` 使用 `conn.send()` 发送心跳消息，不直接访问 `mav.heartbeat_send()`。

需要在 comms/messages.py 中新增一个 `build_heartbeat_msg()` 函数返回可 send 的心跳消息对象。

### D7: forced_strike_point 安全缓冲增强

**选择**: 生成随机点后，计算到最近多边形边的距离（使用 `_point_to_segment_distance` 算法，已在 `safety/geofence.py` 中实现），若小于 buffer_m 则拒绝。

将 `safety/geofence._point_to_segment_distance` 提取为 `utils/geo.py` 的公共函数，供 forced_strike_point 和 Geofence 共用。

## Risks / Trade-offs

- **[R1] python-statemachine 声明式 + 命令式并存**: 两套转换机制可能产生微妙冲突。→ 缓解: 确保 `_perform_transition` 中的 target_state 名字与声明式状态 id 完全一致，且转换在声明式表中已定义。
- **[R2] pymavlink 常量手动维护**: comms/messages.py 中的常量值需与 pymavlink 版本保持一致。→ 缓解: 添加注释标注来源（如 `# pymavlink MAV_CMD_COMPONENT_ARM_DISARM`），单元测试中验证值与 pymavlink 一致。
- **[R3] vision_dispatch 轮询延迟**: 定期轮询 vision_receiver.get_latest() 可能引入延迟。→ 缓解: 轮询间隔设为 100ms，对现有目标跟踪频率足够。
