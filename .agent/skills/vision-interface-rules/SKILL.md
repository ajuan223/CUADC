# 外部解算接口编码规范

本 Skill 约束 `src/striker/vision/` 目录下的所有代码。本模块负责接收外部解算程序给出的目标坐标，以及坐标转换工具。

## 架构约束

- 本模块名称含 "vision" 但实际职责是**外部解算链路**：接收另一个程序计算出的目标坐标
- `VisionReceiver` 是 Protocol (抽象接口)，具体实现有 `TcpReceiver` 和 `UdpReceiver`
- 接收到的坐标数据封装为 `GpsTarget` 数据类，包含 lat/lon/置信度/时间戳
- 坐标校验: 接收到的 GPS 坐标必须通过 `validate_gps()` 验证
- 目标跟踪支持自适应频率：根据目标距离和置信度调整查询频率
- 坐标转换工具库: WGS84 ↔ 局部坐标系转换

### v2.2 变更
- "视觉链路"改称"外部解算链路"，因为实际解算由外部程序负责
- 新增 `point_in_polygon` 和 `forced_strike_point` 工具，服务于强制投弹降级

### 依赖方向
- `vision/` 可依赖: `config/`(连接参数), `exceptions.py`
- `vision/` 被依赖: `core/states/loiter.py`(LOITER 收到坐标 → ENROUTE 转换)
- `vision/` 禁止依赖: `comms/`, `flight/`, `safety/`, `core/machine.py`

### 数据流
- 外部程序 → TCP/UDP → `VisionReceiver.recv()` → `GpsTarget` → `MissionContext`

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `VisionReceiver` | 外部解算接收器 Protocol |
| `TcpReceiver` | TCP 实现 |
| `UdpReceiver` | UDP 实现 |
| `GpsTarget` | 目标坐标数据类 |

## 禁止模式

- **禁止**在本模块中实现图像处理或视觉算法 — 解算由外部程序负责
- **禁止**信任外部程序发来的坐标未经校验 — 必须通过 `validate_gps()` 验证
- **禁止**在接收循环中阻塞事件循环 — 使用 async recv + timeout
- **禁止**硬编码外部程序的 IP/端口 — 必须从 `config/` 读取
- **禁止**忽略坐标时间戳 — 过期坐标（如 > 5 秒）必须标记为无效
