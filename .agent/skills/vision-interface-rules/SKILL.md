# 外部解算接口编码规范

本 Skill 约束 `src/striker/vision/` 目录下的所有代码。本模块负责接收外部视觉系统发送的投弹点坐标。

## 架构约束

- 本模块名称含 "vision" 但实际职责是**外部解算链路**：接收外部视觉系统计算好的投弹点 GPS 坐标
- `VisionReceiver` 是 Protocol (抽象接口)，具体实现有 `TcpReceiver` 和 `UdpReceiver`
- 接收到的坐标数据封装为 `GpsDropPoint` 数据类，包含 lat/lon/置信度/时间戳
- 坐标校验: 接收到的 GPS 坐标必须通过 `validate_gps()` 验证
- `DropPointTracker` 使用滑动窗口中值滤波消除高频抖动，提供平滑后的投弹点坐标
- 投弹点语义: 视觉系统发送的是**投弹点坐标**（payload 应该释放的位置），不是靶标坐标，不需要弹道二次解算

### 依赖方向
- `vision/` 可依赖: `config/`(连接参数), `exceptions.py`
- `vision/` 被依赖: `core/states/scan.py`(扫场完成后投弹点决策), `app.py`(_vision_dispatch 协程)
- `vision/` 禁止依赖: `comms/`, `flight/`, `safety/`, `core/machine.py`

### 数据流
- 外部视觉系统 → TCP/UDP → `VisionReceiver.recv()` → `GpsDropPoint` → `DropPointTracker` → `MissionContext`

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `VisionReceiver` | 外部解算接收器 Protocol |
| `TcpReceiver` | TCP 实现 |
| `UdpReceiver` | UDP 实现 |
| `GpsDropPoint` | 投弹点坐标数据类 |
| `DropPointTracker` | 投弹点跟踪器（滑动窗口中值滤波） |

## 禁止模式

- **禁止**在本模块中实现图像处理或视觉算法 — 解算由外部程序负责
- **禁止**信任外部程序发来的坐标未经校验 — 必须通过 `validate_gps()` 验证
- **禁止**在接收循环中阻塞事件循环 — 使用 async recv + timeout
- **禁止**硬编码外部程序的 IP/端口 — 必须从 `config/` 读取
- **禁止**忽略坐标时间戳 — 过期坐标（如 > 5 秒）必须标记为无效
