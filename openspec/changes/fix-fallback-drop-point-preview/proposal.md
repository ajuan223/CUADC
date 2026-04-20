## Why

Web 场地编辑器的降级投弹点预览硬编码了 `landing.heading_deg` 作为接近/脱离方向，导致无论投弹点放在场地何处，接近线和脱离线始终平行于跑道。而实际飞行后端会根据投弹点位置动态计算接近方向（指向进近点），并在脱离距离上做安全封顶。预览与实际飞行的方向偏差可能误导场地规划。

## What Changes

- 修复 `renderAttackRun()` 的接近方向计算：用 `bearingBetweenPoints(dropPoint, derivedApproach)` 替代硬编码的跑道方向，与后端 `_calculate_approach_heading()` 的优先级 2 逻辑对齐
- 新增脱离距离封顶逻辑：`exit_distance` 不超过 `distance_to_approach - min_handoff_leg_m`，与后端 `_calculate_exit_waypoint()` 对齐
- 投弹点恰好在进近点附近时，回退到跑道方向，与后端优先级 3 一致

## Capabilities

### New Capabilities

### Modified Capabilities

- `field-editor-planning-workflow`: attack run 预览方向和脱离距离需与后端 enroute 状态对齐

## Impact

- `src/field_editor/app.js` — `renderAttackRun()` 函数修改，新增 `haversineDistance` 和 `bearingBetweenPoints` import
- 无 API/依赖变更，纯前端改动
