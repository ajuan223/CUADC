## Context

Striker 项目的飞行场配置目前完全基于手写 JSON 文件（`data/fields/{name}/field.json`）。仓库中的真实模型定义在 `src/striker/config/field_profile.py`：字段包含边界、着陆参数、扫描参数、盘旋点、攻击航线参数与安全缓冲。几何派生逻辑定义在 `src/striker/flight/mission_geometry.py`，包括：

- `derive_landing_approach()`：根据 touchdown / heading / glide slope / approach altitude 反推进近点
- `generate_boustrophedon_scan()`：根据边界与扫描参数生成扫场航线
- `generate_takeoff_geometry()`：根据 runway facts 生成起飞几何

目前仓库没有现成的前端工程，但这个编辑器的需求边界清晰、数据模型稳定，适合做成轻量静态页面。

另一个现实约束是：高德地图 JS API 2.0 不是“只填一个 Key 就结束”，官方初始化流程还需要安全配置；因此编辑器需要显式处理地图凭据输入和持久化。

## Goals / Non-Goals

**Goals:**
- 用户在真实地图上完成 `FieldProfile` 中所有需要人工编辑的空间参数与数值参数配置
- 地图上实时可视化边界、touchdown、派生进近点、盘旋圈、扫描航线
- 导出与现有 `FieldProfile` 模型完全兼容的 `field.json`
- 支持导入已有 `field.json` 继续编辑
- 前端独立运行，不依赖 Striker 后端 API
- 前端预览与校验尽量复用后端已有语义，而不是重新发明一套“看起来像”的规则

**Non-Goals:**
- 不做用户认证 / 权限管理
- 不做与飞控的实时连接、任务上传或 SITL 控制
- 不修改后端 `FieldProfile` schema
- 不在本次变更中实现“直接写入 `data/fields/` 目录”的浏览器能力
- 不为 attack run 构建运行时精确预览（其航向依赖风向 / 当前机位 / 当前 drop point）

## Decisions

### D1: 前端技术选型 — 无构建链的静态页面

**选择**: 使用无构建链的静态前端，放在 `src/field_editor/`，至少拆分为 `index.html`、`app.js`、`styles.css`（必要时增加少量辅助脚本）。

**替代方案**:
- React/Vue SPA：对当前范围过重，会引入 bundler、package manager 与更多维护面
- Python Web 服务：增加运行依赖，但问题本质只是静态 UI
- 所有代码内联到单个 HTML：虽然可行，但对于坐标转换、几何预览和校验逻辑，可维护性偏差

**理由**: 该工具使用频率低但交互逻辑不算短，小型静态页面可以同时保持零构建和基本可维护性。

### D2: 地图服务接入 — 遵循 AMap JS API 2.0 官方加载方式

**选择**: 使用高德地图 JS API 2.0 官方加载方式初始化地图，并支持用户输入 / 更新自己的 Web Key 与安全配置；地图相关插件按需加载。

**理由**:
- 项目面向国内飞行场，高德底图与坐标体系更合适
- 官方文档明确支持地图、覆盖物、MouseTool、PolygonEditor 等能力，足够支撑本编辑器
- 用户自己提供凭据，避免把凭据硬编码进仓库

**实现含义**:
- 编辑器首次打开时先请求地图凭据，而不是盲目初始化地图
- 凭据保存到 `localStorage`，但提供“更新 / 清除凭据”入口
- 地图编辑能力依赖插件加载，而不是自写底层交互

### D3: 坐标处理策略 — 地图内部 GCJ-02，导入导出 WGS84

**选择**: 地图显示与交互使用高德坐标（GCJ-02），导入 / 导出 `field.json` 时统一转换为 / 从 WGS84。

**理由**: 仓库中的 `field.json` 明确使用 WGS84；高德地图显示与用户点击结果是 GCJ-02。转换是必要桥梁，不应把坐标系复杂度暴露给用户。

### D4: 前端状态模型 — 一比一映射当前 `FieldProfile`

**选择**: 浏览器内状态直接镜像当前 `FieldProfile` 结构，不额外设计“前端专用 schema”。

**理由**:
- 导入导出逻辑最简单
- 可以直接对照 `FieldProfile.model_validate()` 做验收
- 能避免当前仓库文档中部分过时字段名对实现造成误导

**特别说明**:
- `attack_run` 作为数值配置对象保留
- `coordinate_system` 固定导出为 `WGS84`
- boundary 导出时写成闭合 polygon（首尾相等）

### D5: 预览逻辑 — 对齐后端几何算法

**选择**: 前端预览不凭感觉画图，而是对齐当前后端已有算法语义：
- landing approach 预览对齐 `derive_landing_approach()`
- scan preview 对齐 `generate_boustrophedon_scan()`

**理由**: 用户看到的预览需要和真正飞行任务生成逻辑尽可能一致，否则编辑器会制造错误信心。

### D6: 覆盖物交互模型 — 用地图原生覆盖物和编辑器能力

**选择**:
- 边界：`Polygon` + 绘制工具 + `PolygonEditor`
- touchdown / loiter：可拖拽 `Marker`
- landing / scan：`Polyline`
- loiter 半径：`Circle`

**理由**: 高德原生覆盖物与编辑器能力已足够，不需要额外绘图库。

### D7: 校验分层 — Blocking vs Advisory

**选择**: 将前端校验分为两层：

**Blocking（禁止导出）**
- geofence 至少 3 个不同顶点
- `safety_buffer_m > 0`
- `landing.runway_length_m > 0`
- touchdown 在 geofence 内
- loiter 点中心在 geofence 内
- landing approach 的派生条件成立：`approach_alt_m > touchdown_alt_m`、推导距离不小于 200m、派生 approach 点在 geofence 内
- scan spacing 为正数

**Advisory（提示但不阻止导出）**
- loiter circle 超出 geofence
- 地图凭据未持久化或被清除后需要重新加载
- 坐标转换存在米级误差

**理由**: Blocking 条件应尽量与当前后端行为或 mission geometry 硬约束一致；其余问题先作为 UX 提示，避免前端比后端更“武断”。

### D8: Attack run UX — 编辑参数，不伪造运行时预览

**选择**: 编辑器提供 `approach_distance_m`、`exit_distance_m`、`release_acceptance_radius_m` 的编辑与导入导出，但不把 attack run 画成“最终将执行的固定航线”。

**理由**: 真实 attack approach heading 在 `src/striker/core/states/enroute.py` 中由运行时条件决定：优先用风向，其次用当前位置到目标点 bearing，最后才回退到 landing heading 反向。静态 field editor 无法预知这些运行时输入。

## Risks / Trade-offs

- **[地图凭据复杂度]** 高德 JS API 2.0 需要 Key 与安全配置，不是纯离线页面即可直接工作。
  - **缓解**: 首次打开给出明确配置引导，并允许本地持久化。

- **[坐标转换误差]** GCJ-02 ↔ WGS84 转换是近似算法，会有米级误差。
  - **缓解**: UI 明示导出为 WGS84，允许用户回读导出的 `field.json` 复检。

- **[仓库文档与代码不完全同步]** 现有部分说明文档仍提到旧字段结构。
  - **缓解**: 以前端实际导入导出要兼容的 Python 模型为唯一权威，不以前置文档为准。

- **[file:// 兼容性]** 某些地图脚本加载方式在 `file://` 下体验不稳定。
  - **缓解**: 使用简单 HTTP 服务访问静态页面作为默认使用方式。
