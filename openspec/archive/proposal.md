## Why

在 `guided_strike` 重构和 `fe-waypoint-exporter` 之后，`field.json` 的职责边界变得不再清晰。目前它内部包含了大量“幽灵字段”（如 `scan.spacing_m`, `landing.glide_slope_deg` 等），这些字段仅在场地编辑器生成 `.waypoints` 时使用，Striker 运行时进程完全不会读取它们。这导致了严重的认知负担：操作员可能误以为修改 `field.json` 中的这些字段会改变飞机的扫描航线或降落轨迹。

为彻底解决此问题，我们需要严格规范 `field.json` 的能力边界：它只应该包含 Striker 运行时和共享所需的决策参数。纯规划阶段的“幽灵分段”将被彻底删除。同时，为了进一步清晰化，我们将在保留的参数旁边增加 JSONC 注释，明确指出这是运行时参数还是共享参数。

## What Changes

- **BREAKING**: 从 `field.json` 和对应的 Pydantic 模型（`FieldProfile`）中彻底删除所有纯规划用途的“幽灵字段”：
  - `scan.spacing_m`
  - `scan.heading_deg`
  - `scan.boundary_margin_m`
  - `landing.glide_slope_deg`
  - `landing.approach_alt_m`
  - `landing.runway_length_m`
  - `landing.use_do_land_start`
- 引入 JSONC（JSON with Comments）支持，通过正则在 Python 侧加载时安全剥离注释。
- 在 `field.json` 中为保留的字段精准添加 `// runtime` 或 `// shared` 等分类注释。
- Field Editor 将不再通过 `field.json` 导出这些纯规划参数，规划参数将被独立剥离（如采用独立的 `planning.json` 或由 Web 状态直接接管）。

## Capabilities

### New Capabilities
- `jsonc-config-support`: 支持加载带有 `//` 注释的 JSONC 格式配置文件
- `field-planning-separation`: 场地规划参数（生成 waypoint 专用）与运行时参数分离

### Modified Capabilities
- `field-profile`: 场地配置数据模型（删除废弃的规划字段，明确字段边界）

## Impact

- `src/striker/config/field_profile.py` — 模型大瘦身，删除多个废弃字段，增加 JSONC 加载支持。
- `src/field_editor/logic.mjs` — `exportFieldProfile` 输出 JSONC 并剔除被废除的规划字段。
- `data/fields/*/field.json` — 现有场地文件被精简并增加注释。
