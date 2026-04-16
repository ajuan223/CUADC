# 安全监控模块编码规范

本 Skill 约束 `src/striker/safety/` 目录下的所有代码。安全监控是 Striker 的生命线，从 ARM 到任务结束始终独立运行。

## 架构约束

- `SafetyMonitor` 是独立协程，通过 `asyncio.create_task()` 启动，与主任务并行运行
- Safety Monitor **永不关闭** (RL-02)：任何异常必须通过降级处理，而非停止监控
- Override 是终态 (RL-03)：人工接管后系统进入 `OverrideState`，**永不自动恢复**自主模式
- 安全检查项: 电池电量、GPS 有效性、心跳超时、空速范围、地理围栏
- 地理围栏使用 `point_in_polygon` 算法实现
- `OverrideDetector` 监测飞控模式切换（如 AUTO → MANUAL/STABILIZE/FBWA）作为 Override 触发信号
- 模式检测使用 `MAVLinkConnection.flightmode` 属性（pymavlink 自动将 HEARTBEAT custom_mode 映射为 ArduPlane 模式名）
- 已接通的检查项: 心跳健康检查、Override 模式检测
- 安全事件 (`EmergencyEvent`, `OverrideEvent`) 直接注入 FSM 全局拦截，不经过业务状态

### 依赖方向
- `safety/` 可依赖: `comms/`(遥测数据), `config/`(阈值), `core/events.py`(事件定义), `exceptions.py`
- `safety/` 被依赖: `core/`(通过事件), `telemetry/`(飞行记录)
- `safety/` 禁止依赖: `flight/`, `payload/`, `vision/`

### 数据流
- 输入: `MissionContext` 中的遥测数据 + `comms/` 心跳状态
- 输出: `EmergencyEvent` / `OverrideEvent` → FSM 全局拦截

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `SafetyMonitor` | 安全监控主协程 |
| `point_in_polygon()` | 点在多边形内判断函数 |
| `check_geofence()` | 围栏校验函数 |

## 禁止模式

- **禁止**在 Safety Monitor 中使用 `try/except` 吞掉异常后 continue — 异常必须通过日志 + 降级处理
- **禁止**将 Safety Monitor 设计为"可暂停"的 — RL-02 红线，协程必须始终存活
- **禁止**Override 后自动恢复自主模式 — RL-03 红线，Override 是终态
- **禁止**安全检查阈值硬编码 — 必须从 `config/` 读取（如低电量阈值、GPS 精度下限）
- **禁止**跳过围栏校验 — 所有位置判断必须通过 `point_in_polygon()`
- **禁止**在 Safety Monitor 中执行长时间阻塞操作 — 检查循环周期不得超过 1 秒
