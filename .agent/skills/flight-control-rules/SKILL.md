# 飞行指令模块编码规范

本 Skill 约束 `src/striker/flight/` 目录下的所有代码。飞行指令层封装所有与飞控交互的高级命令。

## 架构约束

- `FlightController` 是飞行指令的唯一入口，封装 arm/takeoff/goto/set_mode/set_speed/upload_mission
- 飞行模式使用 `ArduPlane` 模式枚举 (`MANUAL`, `FBWA`, `AUTO`, `GUIDED`, `LOITER`, `RTL` 等)
- 航点上传遵循 MAVLink Mission Micro-Protocol 三阶段：握手(清空+宣告) → 逐条响应 → 终盘确认
- 完整任务由程序化几何生成：起飞、扫描、攻击、降落均从 `FieldProfile` 参数推导，而不是读取静态 `scan_waypoints`
- 降落序列从 `FieldProfile.landing` 读取参数，在起飞前通过 Mission Protocol 上传到飞控
- 攻击任务和降落-only 任务会在状态推进过程中二次上传，飞控执行的 mission 以当前上传结果为准
- 固定翼特性：不能悬停，所有转向基于航点航线，降落需要进近航点和下滑道参数
- `mission_geometry.py`、`navigation.py`、`landing_sequence.py` 负责飞行几何；`mission_upload.py` 负责把几何变成 mission items

### MAVLink Mission Protocol 要点
1. 发送 `MISSION_CLEAR_ALL` + 等待 `MISSION_ACK`
2. 发送 `MISSION_COUNT` (宣告总数)
3. **按飞控请求的 index** 发送对应 `MISSION_ITEM`（飞控具有主动权）
4. 等待最终 `MISSION_ACK` 确认

### 依赖方向
- `flight/` 可依赖: `comms/`(MAVLink 连接), `config/`(飞行参数), `exceptions.py`
- `flight/` 被依赖: `core/states/`(业务状态调用飞行指令)
- `flight/` 禁止依赖: `core/`, `safety/`, `payload/`, `vision/`

### 数据流
- 输入: `FlightController` 接收高层指令 (goto 坐标、upload 航点列表)
- 输出: 通过 `comms/` 发送 MAVLink 命令到飞控

## 注册模式

| 注册项 | 说明 |
|--------|------|
| `FlightController` | 飞行指令控制器 |
| `generate_mission_geometry()` | 程序化任务几何生成 |
| `upload_mission_items()` | 航点上传函数 |
| `generate_landing_sequence()` | 降落序列生成函数 |

## 禁止模式

- **禁止**在 Mission Protocol 中盲目循环发送 `MISSION_ITEM` — 必须按飞控请求的 index 响应
- **禁止**跳过 Mission Protocol 握手阶段 — 必须先清空再宣告总数
- **禁止**硬编码航点坐标 — 所有几何必须从 `FieldProfile` 参数推导
- **禁止**在飞行指令中直接处理安全逻辑 — 安全检查由 Safety Monitor 独立负责
- **禁止**发送 MAVLink 命令前不检查连接状态 — 必须确认心跳正常
- **禁止**忽略 `MISSION_ACK` 返回值 — 上传失败必须抛出 `MissionUploadError`
- **禁止**继续描述“场地文件内预定义 scan_waypoints”作为当前主流程 — 当前主流程是程序化扫描生成
