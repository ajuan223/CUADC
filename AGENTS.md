# AGENTS.md — Striker AI 编码宪法

本文件为 AI Agent 在 Striker 项目中的强制编码规范。所有触及 `src/striker/` 的代码变更必须遵守。
个人风格偏好写入 `AGENTS.local.md`（已 gitignore），但 Red Lines (RL-01~RL-10) 和安全规则不可被覆盖。

---

## R01 命名约定

- 模块/文件: ✓ `flight_controller.py` / ✗ `flightController.py`
- 类: ✓ `MissionStateMachine` / ✗ `mission_stateMachine`
- 常量: ✓ `MISSION_ITEM_REACHED` / ✗ `MissionItemReached`
- 函数/变量: ✓ `validate_gps()` / ✗ `validateGps()`

## R02 类型标注

`mypy --strict` 零容忍。所有函数参数 + 返回值必须有类型注解，变量在推断不足时显式标注。

## R03 Import 顺序

stdlib → 第三方 → 本地，空行分隔。`ruff check --select I` 强制排序。

## R04 日志规范

仅使用 `structlog`。`print()` 和 `logging` 在 `src/` 中**禁止**（`tests/` 中 print 例外）。

## R05 严禁盲目落码

新增/修改模块前**必须**先代码搜索调研，检查已有实现，确认无重复。

## R06 能力发现优先

实现通用函数前**必须**先查 `REGISTRY.md`，优先复用已注册能力。

## R07 包治理防腐墙

`pkg/` 变更必须 version bump + `REGISTRY.md` 同步更新。禁止 `src↔pkg` 和 `pkg↔pkg` 双向依赖。

## R08 Skill 路由表

触及下方目录时，加载对应 Skill：

| 源码目录 | Skill |
|----------|-------|
| `src/striker/core/` | `core-fsm-rules` |
| `src/striker/comms/` | `comms-mavlink-rules` |
| `src/striker/flight/` | `flight-control-rules` |
| `src/striker/safety/` | `safety-monitor-rules` |
| `src/striker/vision/` | `vision-interface-rules` |
| `src/striker/payload/` | `payload-release-rules` |
| `src/striker/config/` | `config-system-rules` |
| `src/striker/telemetry/` | `telemetry-rules` |
| `src/striker/utils/` | `utils-rules` |
