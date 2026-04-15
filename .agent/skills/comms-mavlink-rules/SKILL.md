# MAVLink 通信层编码规范

本 Skill 约束 `src/striker/comms/` 目录下的所有代码。通信层是 Striker 与飞控之间的唯一桥梁，负责连接管理、心跳监控、消息收发和遥测解析。

## 架构约束

- pymavlink 是 MAVLink 协议的**唯一**入口，封装在 `comms/` 内部
- `MAVLinkConnection` 是连接管理的核心类，支持串口 (921600 baud) 和 UDP (SITL)
- 遵循 Producer-Consumer 模式：独立 `_rx_loop()` 协程 + `asyncio.Queue` 消息分发
- 遥测数据在 `comms/telemetry.py` 内**立即**转换为强类型 dataclass（如 `GeoPosition`），上层业务逻辑不接触原始 pymavlink 报文
- 心跳监控基于 MAVLink `HEARTBEAT` 报文实现软看门狗，不依赖 socket 存活判断
- GPS 坐标工程单位转换（`lat/1e7`, `alt/1000.0`）必须在 comms 层完成

### 依赖方向
- `comms/` 可依赖: `config/`(连接参数), `exceptions.py`, pymavlink
- `comms/` 被依赖: `flight/`, `safety/`, `core/`, `telemetry/` — 但上层**仅通过 comms 公共接口访问**
- `comms/` 禁止依赖: `core/`, `flight/`, `safety/`, `payload/`, `vision/`

### 数据流
- 下行: 飞控 → pymavlink → `_rx_loop()` → `asyncio.Queue` → 消息路由 → 遥测 dataclass → `MissionContext`
- 上行: 业务层 → comms 公共接口 `send()` → pymavlink → 飞控

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `MAVLinkConnection` | MAVLink 连接管理类 |
| `GeoPosition` | 地理位置数据类 |
| `validate_gps()` | GPS 坐标校验函数 |

## 禁止模式

- **禁止**在 `comms/` 以外的任何模块直接 `import pymavlink` — 这是 RL-04 红线
- **禁止**在协程中使用 `blocking=True` 的 pymavlink 调用 — 必须用 `blocking=False` + `asyncio.sleep`
- **禁止**向上层暴露原始 pymavlink 报文对象 — 必须在 comms 层转换为强类型
- **禁止**跳过心跳看门狗 — 连接健康判断必须基于 HEARTBEAT 超时
- **禁止**在 `_rx_loop()` 中 sleep 超过 5ms — 否则吞吐量不足
- **禁止**硬编码串口参数 — 必须从 `config/` 读取
