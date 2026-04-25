## 1. 基础设施：MAVLink 协议扩展

- [x] 1.1 在 `flight/mission_upload.py` 中实现 `partial_write_mission()` — MISSION_WRITE_PARTIAL_LIST 协议（发送 partial list → 响应 MISSION_REQUEST_INT → 验证 MISSION_ACK）
- [x] 1.2 在 `flight/mission_upload.py` 中实现 `download_mission()` — Mission Download Protocol（MISSION_REQUEST_LIST → 逐条 MISSION_REQUEST_INT → 收集所有 MISSION_ITEM_INT）
- [x] 1.3 在 `comms/messages.py` 中补充缺失的 MAVLink 常量（MISSION_WRITE_PARTIAL_LIST、MISSION_REQUEST_LIST、MAV_CMD_NAV_LOITER_UNLIM=17 等）
- [x] 1.4 新增 `MissionDownloadError` 异常类到 `exceptions.py`

## 2. 视觉接口重构

- [x] 2.1 新建 `vision/global_var.py` — 定义 `VISION_DROP_POINT` 全局变量、`threading.Lock`、`set_vision_drop_point()` / `get_vision_drop_point()` 线程安全函数
- [x] 2.2 为 `global_var.py` 添加 GPS 坐标校验（复用 `vision/models.py` 中的 `validate_gps()`）

## 3. 任务解析数据结构

- [x] 3.1 新建 `flight/preburned_mission.py` — 定义 `PreburnedMissionInfo` dataclass（loiter_seq, slot_start_seq, slot_end_seq, landing_start_seq, total_count）
- [x] 3.2 在 `flight/preburned_mission.py` 中实现 `parse_preburned_mission(items) -> PreburnedMissionInfo` — 扫描 mission items 找到关键 seq 并校验结构
- [x] 3.3 更新 `core/context.py` — 新增 `preburned_info: PreburnedMissionInfo | None` 字段，移除不再需要的 `scan_start_seq` / `scan_end_seq` / `attack_geometry` 字段

## 4. 状态机重构

- [x] 4.1 更新 `core/machine.py` — 定义新状态名（init, standby, scan_monitor, loiter_hold, attack_run, release_monitor, landing_monitor, completed, override, emergency）和转换链
- [x] 4.2 新建 `core/states/standby.py` — StandbyState：调用 download_mission() → parse_preburned_mission() → 校验通过后转 scan_monitor
- [x] 4.3 重写 `core/states/scan.py` → `core/states/scan_monitor.py` — ScanMonitorState：纯监听 mission_current_seq，到达 loiter_seq 时转 loiter_hold
- [x] 4.4 新建 `core/states/loiter_hold.py` — LoiterHoldState：读取 vision 全局变量 → 决定投弹点 → 计算 approach/exit → partial_write_mission() → MISSION_SET_CURRENT → 转 attack_run
- [x] 4.5 重写 `core/states/enroute.py` → `core/states/attack_run.py` — AttackRunState：监听飞机飞向投弹点进度，target seq 通过后转 release_monitor
- [x] 4.6 重写 `core/states/release.py` → `core/states/release_monitor.py` — ReleaseMonitorState：确认 DO_SET_SERVO 已由飞控自动执行（在 mission 中），转 landing_monitor
- [x] 4.7 重写 `core/states/landing.py` → `core/states/landing_monitor.py` — LandingMonitorState：移除 upload_landing_mission() 调用，纯监听 STATUSTEXT + 高度判断落地

## 5. 攻击几何简化

- [x] 5.1 在 `flight/mission_geometry.py` 或新文件中实现简化版 attack geometry — 只计算 approach 和 exit 航点（不需要 boustrophedon、takeoff、landing 解算）
- [x] 5.2 在 `loiter_hold.py` 中实现 slot 构建逻辑 — 生成 5 个 mission item（approach NAV_WP, target NAV_WP, DO_SET_SERVO, exit NAV_WP, spare NAV_WP）

## 6. 应用层适配

- [x] 6.1 更新 `app.py` — 注册新状态实例（StandbyState, ScanMonitorState, LoiterHoldState, AttackRunState, ReleaseMonitorState, LandingMonitorState），移除旧状态
- [x] 6.2 更新 `app.py` — 调整 vision receiver 初始化（移除 TcpReceiver 创建和 _vision_dispatch 协程，改为导入 global_var）
- [x] 6.3 更新 `core/states/__init__.py` — 注册新状态名到 state registry

## 7. 代码清理

- [x] 7.1 删除 `core/states/preflight.py`
- [x] 7.2 删除 `core/states/takeoff.py`
- [x] 7.3 删除旧的 `core/states/scan.py`（被 scan_monitor.py 替代后）
- [x] 7.4 删除旧的 `core/states/enroute.py`（被 attack_run.py 替代后）
- [x] 7.5 从 `flight/mission_upload.py` 中删除 `upload_full_mission()` / `upload_attack_mission()` / `upload_landing_mission()`
- [x] 7.6 从 `flight/mission_geometry.py` 中删除 `generate_boustrophedon_scan()` / `generate_takeoff_geometry()` / `generate_mission_geometry()` / `derive_landing_approach()`
- [x] 7.7 从 `flight/navigation.py` 中删除 `build_waypoint_sequence()` / `build_attack_run_mission()` / `build_landing_only_mission()`
- [x] 7.8 删除 `flight/landing_sequence.py`（landing 序列预烧录，不再生成）
- [x] 7.9 清理 `core/context.py` 中已废弃的字段和 `last_scan_waypoint` 属性

## 8. SITL 测试适配

- [x] 8.1 编写 `scripts/burn_mission.py`（可选/或手动编写 `.waypoints` 文件） — 生成包含起飞、航线、无限盘旋（NAV_LOITER_UNLIM）及降落航点的全套测试航线文件。
- [x] 8.2 更新 `scripts/run_sitl.sh` — 增加加载 `.waypoints` 文件的逻辑或文档说明，适配新测试流程。
- [x] 8.3 执行集成测试：验证飞机能自动完成 takeoff (由 mission 触发) -> 抵达 loiter 圈等待 -> Python 注入投弹点并 unblock -> 执行 attack run -> landing。
