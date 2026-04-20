## Context

Web 场地编辑器 (`src/field_editor/app.js`) 的 `renderAttackRun()` 用 `landing.heading_deg` 硬编码降级投弹点的接近/脱离方向。Python 后端 (`src/striker/core/states/enroute.py`) 的 `_calculate_approach_heading()` 有三级动态逻辑（逆风→方位角→跑道方向），`_calculate_exit_waypoint()` 还会封顶脱离距离避免越过进近点。Web 预览和实际飞行路径不一致。

## Goals / Non-Goals

**Goals:**
- Web attack run 预览的接近方向与后端 `_calculate_approach_heading()` 优先级 2-3 对齐（跳过逆风，因 Web 无风速数据）
- Web attack run 预览的脱离距离与后端 `_calculate_exit_waypoint()` 封顶逻辑对齐

**Non-Goals:**
- 不修改 Python 后端算法
- 不实现逆风接近预览（静态预览无风速输入）
- 不修改 `logic.mjs` 的几何计算函数（只改 `app.js` 的调用方式）

## Decisions

### D1: 在 `renderAttackRun()` 中内联方向计算

直接在 `renderAttackRun()` 里用 `derivedApproach`（已有）计算 `bearingBetweenPoints(dropPoint, derivedApproach)`，不引入新函数。逻辑分支与后端 `_calculate_approach_heading()` 一致：

1. 计算投弹点到进近点距离
2. 距离 ≤ 30m 时用跑道方向（后端 `MIN_NEAR_APPROACH_LEG_M`）
3. 否则用 `bearing(dropPoint → approach)`

**替代方案**：在 `logic.mjs` 加通用函数。拒绝理由——这是单点 UI 逻辑，不涉及复用。

### D2: 脱离距离封顶用相同阈值

复用后端 `_calculate_exit_waypoint()` 的封顶公式：

```
min_handoff = max(30, min(approach_distance_m, runway_length_m))
max_safe_exit = max(0, distance_to_approach - min_handoff)
capped_exit = min(exit_distance_m, max_safe_exit)
```

封顶时在预览中无特殊提示——后端也没有提示，只是静默截断。

### D3: 新增 `haversineDistance` 和 `bearingBetweenPoints` import

这两个函数已存在于 `logic.mjs`，只需在 `app.js` 的 import 列表中添加。

## Risks / Trade-offs

- [投弹点在场外时 derivedApproach 可能为 null] → 已有 null 检查跳过渲染，无影响
- [封顶后脱离线可能极短甚至为 0] → 与后端行为一致，忠实反映实际飞行
