## Why

当前飞行场配置（`data/fields/{name}/field.json`）完全依赖手动编辑 JSON 文件。用户需要理解 WGS84 坐标、闭合多边形围栏、着陆几何、扫描参数和攻击航线参数的语义，才能正确配置一个飞行场。这导致：(1) 新场地配置门槛高、易出错；(2) 地理坐标无法直观校验；(3) 边界、着陆、扫描、盘旋等要素的空间关系难以可视化。

需要一个基于高德地图的前端编辑器，让用户在真实地图上通过点击、拖拽和表单输入完成场地配置，替代手工 JSON 编辑。

## What Changes

- 新增一个独立的静态 Web 前端应用（field editor），用于编辑当前仓库实际使用的 `FieldProfile` 结构：
  - `boundary.polygon`
  - `landing.touchdown_point / heading_deg / glide_slope_deg / approach_alt_m / runway_length_m / use_do_land_start`
  - `scan.altitude_m / spacing_m / heading_deg`
  - `loiter_point.lat / lon / alt_m / radius_m`
  - `attack_run.approach_distance_m / exit_distance_m / release_acceptance_radius_m`
  - `safety_buffer_m`
- 前端基于高德地图提供可视化编辑与实时预览：
  - 绘制和编辑 geofence boundary
  - 放置 touchdown / loiter 点
  - 预览派生的 landing approach gate
  - 预览 scan path 与 loiter circle
- 前端支持导入已有 `field.json` 进行编辑，并导出与当前 `FieldProfile` Pydantic 模型兼容的 JSON。
- 前端在浏览器中执行与当前后端一致的关键校验，并补充少量仅用于 UX 的 advisory warning。
- 攻击航线参数在前端以数值方式编辑和导入导出；不要求前端给出“真实运行时”攻击路径，因为实际攻击进场航向依赖运行时风向与飞机当前位置。

## Capabilities

### New Capabilities
- `field-map-editor`: 基于高德地图的飞行场可视化编辑前端，支持地图绘制、关键点拖拽、参数编辑、实时预览、导入导出 `field.json`

### Modified Capabilities
- `field-profile`: 无 schema 级变更。前端输出的 JSON 必须与现有 `FieldProfile` 模型完全兼容，后端代码无需为该编辑器调整数据结构。

## Impact

- **新增代码**：静态前端资源，建议位于 `src/field_editor/`
- **外部依赖**：高德地图 JS API 2.0；用户需要提供自己的 Web Key 及安全配置
- **后端无 schema 变更**：以 `src/striker/config/field_profile.py` 为数据格式权威
- **构建/部署**：前端无需引入 SPA 构建链，可通过简单本地 HTTP 服务打开并使用
- **验证基线**：导出的 JSON 需要能通过 `FieldProfile.model_validate()`，且预览逻辑需要与 `mission_geometry.py` 中现有算法一致