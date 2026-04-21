# 飞行指令模块编码规范

本 Skill 约束 `src/striker/flight/` 目录下的所有代码。飞行指令层封装所有与飞控交互的高级命令。

## 架构约束

- `FlightController` 是飞行指令的唯一入口，封装 arm/takeoff/goto/set_mode/set_speed/upload_mission
- 飞行模式使用 `ArduPlane` 模式枚举 (`MANUAL`, `FBWA`, `AUTO`, `GUIDED`, `LOITER`, `RTL` 等)
- 主流程改为 **GUIDED 主动导航与投弹**：飞控预烧录完整任务（含起飞、扫场）。Striker 仅负责在扫场完成后切入 GUIDED 模式，接管飞控，并程序化下发 `DO_REPOSITION` 与 `DO_SET_SERVO`。
- `attack_geometry.py` 负责仅针对投弹阶段（approach / exit）的局部航点计算
- `mission_upload.py` 负责全量上传与下载预烧录任务

### MAVLink Mission Protocol 要点
1. **全量上传**: 发送 `MISSION_CLEAR_ALL` + 宣告总数 + 逐条响应 + 最终 ACK
2. **任务下载** (`download_mission`): 发送 `MISSION_REQUEST_LIST` + 接收总数 + 逐条 `MISSION_REQUEST_INT` + 响应 `MISSION_ACK`

### 依赖方向
- `flight/` 可依赖: `comms/`(MAVLink 连接), `config/`(飞行参数), `exceptions.py`, `utils/geo.py`
- `flight/` 被依赖: `core/states/`(业务状态调用飞行指令)
- `flight/` 禁止依赖: `core/`, `safety/`, `payload/`, `vision/`

### 数据流
- 输入: `FlightController` 接收高层指令 (goto 坐标、upload 航点列表)
- 输出: 通过 `comms/` 发送 MAVLink 命令到飞控

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `FlightController` | 飞行指令控制器 |
| `upload_mission()` | 全量航点上传函数 |
| `download_mission()` | 执行任务下载的协议函数 |
| `parse_preburned_mission()`| 解析下载的预烧录任务提取关键 seq |
| `PreburnedMissionInfo` | 预烧录任务关键位置数据模型 |

## 禁止模式

- **禁止**在 Mission Protocol 中盲目循环发送 `MISSION_ITEM` — 必须按飞控请求的 index 响应
- **禁止**在飞行指令中直接处理安全逻辑 — 安全检查由 Safety Monitor 独立负责
- **禁止**发送 MAVLink 命令前不检查连接状态 — 必须确认心跳正常
- **禁止**忽略 `MISSION_ACK` 返回值 — 上传/覆写失败必须抛出 `MissionUploadError`
- **禁止**继续描述“程序化全量扫描生成”作为当前主流程 — 现在的扫描路径通过 Mission Planner 预烧录在飞控内
