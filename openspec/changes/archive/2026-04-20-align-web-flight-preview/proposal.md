## Why

Web 场地编辑器的飞行路径预览与 Python 后端实际飞行算法存在偏差：扫描路径缺少 inset 和 midpoint check，起飞 climbout 点画远了 1 倍，且起飞路径和段间连接完全缺失。用户无法信任"所见即所飞"，可能导致场地规划时的误判。

## What Changes

- 修复扫描路径算法：补齐 endpoint inset（`min(5, max(width/10, 1))` 米内缩）和 segment midpoint polygon inclusion check，与 Python `mission_geometry.py` 1:1 对齐
- 修复起飞 climbout 距离 bug：从 `1.0×runway_length_m` 改为 `0.5×runway_length_m`，与 Python `generate_takeoff_geometry` 一致
- 新增起飞路径可视化：画出 takeoff start → climbout 线段
- 新增段间连接线：climbout → scan 首点、scan 末点 → landing approach，用灰色虚线表示飞行顺序
- 投弹预览标注：在 attack run 可视化上标明"静态预览（实际方向可能不同）"

## Capabilities

### New Capabilities

- `field-editor-flight-preview`: 完整任务链路可视化（起飞路径、段间连接、投弹预览标注），让用户在编辑器中看到完整的飞行顺序

### Modified Capabilities

- `field-editor-planning-workflow`: 扫描路径算法和起飞 climbout 计算需与后端对齐
- `fixed-wing-takeoff-sequence`: climbout 距离因子从 1.0× 修正为 0.5×（仅 JS 端）

## Impact

- `src/field_editor/logic.mjs` — `generateBoustrophedonScan`、`deriveTakeoffPreview` 函数修改
- `src/field_editor/app.js` — `renderOverlays`、`renderScanPreview`、新增 `renderTakeoffPath`、`renderMissionChain`、`renderAttackRun` 修改
- 无 API/依赖变更，纯前端改动
