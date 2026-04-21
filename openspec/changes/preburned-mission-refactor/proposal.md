## Why

Striker 当前全权控制航点生命周期：从地理围栏和跑道配置解算 takeoff/scan/landing 完整航点序列，动态上传飞控。这种架构在比赛场景中存在严重风险——现场如果 Striker 上传失败或算法出错，飞机无法执行任何任务。终章要求航点序列预烧录在飞控中（通过 Mission Planner 规划），Striker 仅接管扫场结束到降落之间的投弹决策段，通过 `MISSION_WRITE_PARTIAL_LIST` 覆写预留槽位实现动态投弹点插入，大幅降低系统复杂度和现场故障面。

## What Changes

- **BREAKING**: 移除全量航点解算和上传流程（`generate_mission_geometry` 全流程、`upload_full_mission`、`upload_attack_mission`、`upload_landing_mission`）
- **BREAKING**: 移除 Preflight 任务上传和 Takeoff arm/takeoff 指令发送——飞控预烧录任务由人工/Mission Planner 管理
- **BREAKING**: 状态机从 `INIT→PREFLIGHT→TAKEOFF→SCAN→ENROUTE→RELEASE→LANDING→COMPLETED` 重构为 `INIT→STANDBY→SCAN_MONITOR→LOITER_HOLD→ATTACK_RUN→RELEASE_MONITOR→LANDING_MONITOR→COMPLETED`
- 新增 `MISSION_WRITE_PARTIAL_LIST` 局部覆写能力——在飞行中覆写预留航点槽位
- 新增 `MISSION_REQUEST_LIST` / `MISSION_REQUEST_INT` 任务下载能力——启动时从飞控读取预烧录任务并解析关键 seq
- 新增 `LOITER_HOLD` 状态——检测飞机进入预烧录的 `NAV_LOITER_UNLIM` 后，从视觉全局变量读取投弹坐标（或降级点），覆写槽位，`MISSION_SET_CURRENT` 解除阻塞
- 视觉接口从 TCP receiver 改为进程内 Python 全局变量（`VISION_DROP_POINT: tuple[float, float] | None`）
- 预留 5 个航点槽位（approach + target + DO_SET_SERVO + exit + spare）

## Capabilities

### New Capabilities
- `mission-partial-write`: MAVLink `MISSION_WRITE_PARTIAL_LIST` 协议实现，支持飞行中局部覆写指定 seq 范围的航点
- `mission-download`: MAVLink Mission Download Protocol 实现，启动时从飞控读取已有任务并解析关键序号
- `loiter-hold-inject`: LOITER_HOLD 状态核心逻辑——检测盘旋、读取投弹坐标、覆写槽位、解除阻塞
- `vision-global-var`: 视觉投弹点全局变量接口，替代 TCP receiver

### Modified Capabilities
- `business-states`: 状态机流程从全权控制重构为旁路注入模式，状态名和转换链全部重定义
- `mission-upload`: 移除全量上传流程，保留基础 `upload_mission` 协议，新增 partial write
- `procedural-mission-geometry`: 移除 boustrophedon scan / takeoff geometry / landing approach 解算，仅保留 attack run 简化计算（approach/exit 航点）
- `drop-point-routing`: 投弹点决策从 scan 状态移入 loiter-hold 状态，降级点来源改为 field_profile 配置
- `vision-receiver`: 从外部 TCP/UDP 接收改为进程内全局变量读取

## Impact

- **src/striker/core/**: 状态机定义和全部 state 文件重写
- **src/striker/flight/**: mission_geometry.py 大幅精简，mission_upload.py 新增 partial write / download，navigation.py 精简
- **src/striker/vision/**: tracker.py 简化，tcp_receiver.py 可能废弃，新增全局变量接口
- **src/striker/app.py**: 状态注册、vision receiver 初始化逻辑调整
- **src/striker/core/context.py**: 新增 loiter_seq / slot seq 等字段，移除 scan geometry 相关字段
- **data/fields/**: field profile 可能需要新增 `loiter_seq` / `slot_count` 等配置字段
- **不影响**: comms/、safety/、telemetry/、utils/、payload/（释放机构）、field_editor/
