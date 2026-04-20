# v0.0.3 — 2026-04-18

## 概述

本版本修复了 SITL 全链路飞行中扫描边界越界、起飞方向偏移、巡航速度失效、投弹点坐标系偏移等关键问题，并完善了场地编辑器的攻击航线编辑和预览功能。SITL 全链路（起飞 → 扫描 → 进近 → 投弹 → 降落）首次在 zjg2 场地完整通过。

## 修复

### 扫描多边形内缩算法 (`mission_geometry.py`)

- **重写 `_shrink_polygon()`**：原算法计算的是边的切线方向而非内法线方向，导致所有内缩顶点都在原始多边形外。新算法使用邻边内法线平分线 + 质心方向验证 + 二分搜索回退，确保每个内缩顶点都在多边形内。
- **扫描线段中点校验**：扫描线生成时增加中点是否在多边形内的判断，过滤掉跨越凹角的无效线段，端点微量内收保证合法。

### 起飞方向与安全围栏 (`navigation.py`, `monitor.py`)

- **ArduPlane 起飞方向问题**：ArduPlane SITL 始终沿 `--home` 航向起飞（153.7° SSE），忽略 `MAV_CMD_NAV_TAKEOFF` param4。起飞几何改为使用跑道实际航向，不再做反向假设。
- **围栏检查门控**：安全监控器仅在飞机到达第一个扫描航点后启用围栏检查（`reached_scan` 门控），避免起飞→扫描过渡阶段的误报。起飞路径沿跑道方向，在围栏保护范围外但属于正常飞行阶段。
- **增加飞行状态分类**：`_AIRSPEED_CHECK_STATES`（空速检查）和 `_FLIGHT_STATES`（电池/围栏检查），不同阶段启用不同检查组合。

### 巡航速度配置 (`settings.py`, `takeoff.py`)

- 新增 `cruise_speed_mps` 配置项（默认 12 m/s），支持环境变量 `STRIKER_CRUISE_SPEED_MPS` 三层覆盖（环境变量 → config.json → 代码默认值）。
- 起飞到达目标高度后自动发送 `DO_CHANGE_SPEED` 指令，之前飞机以 ArduPlane 默认 22 m/s 飞行。

### 投弹点坐标系转换 (`logic.mjs`)

- **修复致命 bug**：Web 编辑器导出 `field.json` 时，`fallback_drop_point` 未做 GCJ-02→WGS84 坐标转换，而 boundary 和 touchdown 均已转换。导致运行时投弹点偏移约 500m，触发 geofence emergency。
- 同步修复导入逻辑：WGS84 field.json 导入时 drop point 也需做 WGS84→GCJ-02 转换。

### SITL 调试链路 (`run_sitl.sh`)

- **一键启动**：`run_sitl.sh` 改为全自动启动 SITL → MAVProxy → Striker，不再需要手动开终端。
- MAVProxy 就绪后等待 20s 再启动 Striker，确保 GPS 锁定、EKF 对齐、空速校准完成。
- Striker 日志实时输出到终端（`PYTHONUNBUFFERED` + `python -u`），同时写入 `striker.log`。
- Flight log 正确保存到目标路径（通过 `STRIKER_RECORDER_OUTPUT_PATH` 环境变量）。
- 进程清理统一管理，Ctrl+C 一次停止全部。

## 新功能

### 场地编辑器 — 攻击航线编辑

- **降级投弹点地图点选**：新增"设置降级投弹点"工具栏按钮，点击后进入地图交互模式，点选位置即设为投弹点坐标。标记可拖动调整。
- **攻击航线可视化**：投弹点设定后，地图显示攻击进近线（橙色虚线）和脱离线（紫色虚线），长度由 `approach_distance_m` 和 `exit_distance_m` 控制。
- **面板汉化**：Attack Run 面板标签全部翻译为中文（进近距离、脱离距离、投弹容差半径、降级投弹点）。
- **投弹点字段只读化**：Lat/Lon 输入框改为 readonly，只能通过地图点选设置，避免手动输入错误坐标。

### 扫描边界余量 — 统一配置

- `scan.boundary_margin_m` 从全局配置 (`settings.py`) 迁移为场地级参数（`field.json` 的 `scan` 字段），默认 100m。
- 前端编辑器新增"边界余量"输入框，预览扫描路线时使用该值做多边形内缩，与运行时行为一致。
- 前端新增 `shrinkPolygon()` 算法（与后端 `_shrink_polygon` 一致的平分线法），在局部米制坐标系下计算。

### 投弹点降级策略

- 投弹点来源优先级：外部视觉传入 → field.json 的 `fallback_drop_point` → 几何质心。
- `AttackRunConfig` 新增 `fallback_drop_point: GeoPoint | None` 字段。

### Agent 规范体系

- 新增 `.agent/Agent.md` 路由表，按后端模块/Web 前端/SITL 仿真/OpenSpec 工作流/通用 五类索引全部 24 个 skill。
- 新增 `.agent/skills/field-editor-rules/SKILL.md`，GCJ-02/WGS84 坐标转换红线约束。
- 新增 `.agent/skills/sitl-autodebug-loop/SKILL.md`，SITL 自动调试循环规范。
- 各模块 SKILL.md 同步更新以匹配代码现状。

## 文件变更统计

73 files changed, +2305 -218

### 关键文件

| 文件 | 变更 |
|------|------|
| `src/striker/flight/mission_geometry.py` | 重写多边形内缩算法、起飞几何、扫描线中点校验 |
| `src/striker/flight/navigation.py` | 起飞航向参数、DO_CHANGE_SPEED 支持 |
| `src/striker/safety/monitor.py` | reached_scan 围栏门控、飞行状态分类 |
| `src/striker/config/field_profile.py` | boundary_margin_m 迁移为场地参数 |
| `src/striker/config/settings.py` | cruise_speed_mps、移除 scan_boundary_margin_m |
| `src/striker/core/states/scan.py` | 扫描完成逻辑、降级投弹点选取 |
| `src/striker/core/states/landing.py` | 降落走廊延迟激活 |
| `src/field_editor/logic.mjs` | shrinkPolygon、坐标转换修复、boundary_margin_m |
| `src/field_editor/app.js` | 投弹点地图点选、攻击航线可视化 |
| `src/field_editor/index.html` | 工具栏按钮、面板汉化、边界余量输入 |
| `scripts/run_sitl.sh` | 一键启动、日志实时输出、进程清理 |
| `data/fields/zjg2/field.json` | 修正投弹点 WGS84 坐标、新增 boundary_margin_m |

## 测试

- ruff check: passed
- mypy: passed
- pytest: 257 passed
- SITL 全链路: takeoff → scan(10 waypoints, 4 sweeps) → enroute → release(dry-run) → landing → completed
