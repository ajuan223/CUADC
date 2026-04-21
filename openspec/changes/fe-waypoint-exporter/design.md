## Context

Field Editor 是基于 AMap 的 Web 地图编辑器，使用 GCJ-02 坐标系交互，导出 WGS84 配置。当前架构：

- `logic.mjs` — 纯计算：扫描路径生成 (`generateBoustrophedonScan`)、起降推导 (`deriveLandingApproach`/`deriveTakeoffPreview`)、坐标转换、校验
- `app.js` — UI 交互：AMap overlay 管理、事件绑定、`handleExport()` → `field.json`
- `validateFieldProfile()` 内部已生成 `scanPreview[]`、`derivedApproach`、`derivedTakeoff` — 这些是构建完整飞控任务的全部航点数据

Striker 后端通过 `preburned_mission.py` 解析预烧录任务，期望结构：`NAV_LOITER_UNLIM` (盘旋等待) → `DO_LAND_START` → `NAV_LAND`。

## Goals / Non-Goals

**Goals:**
- FE 一键导出 `.waypoints` 文件 (QGC WPL 110)，可直接导入 Mission Planner / QGC / MAVProxy 并上传飞控
- FE 一键导出 `.poly` geofence 文件，可直接导入 Mission Planner
- 用户可自定义 LOITER_UNLIM 盘旋点位置（默认在最后一个扫描航点）
- 保留 `field.json` 导出作为并行选项
- 所有导出坐标正确通过 GCJ-02 → WGS84 转换

**Non-Goals:**
- 不改造 Striker 后端，后端仍从 `field.json` 加载
- 不引入新的 npm 依赖或构建工具
- 不实现 `.waypoints` 文件的导入（反向解析）
- 不实现任务上传/飞控通信（这是 Striker 的职责）
- 不修改 `attack_run` 相关运行时逻辑

## Decisions

### D1: 任务序列结构

**决定**：采用与 `preburned_mission.py` 兼容的固定序列：

```
seq 0: HOME (NAV_WAYPOINT 16)     ← touchdown_point, frame=0, alt=0
seq 1: NAV_TAKEOFF (22)           ← pitch=15°, alt=scan_altitude, frame=3
seq 2..N: NAV_WAYPOINT (16)       ← scanPreview[], frame=3
seq N+1: NAV_LOITER_UNLIM (17)    ← 盘旋等待, frame=3
seq N+2: DO_LAND_START (189)      ← 降落标记
seq N+3: NAV_WAYPOINT (16)        ← derivedApproach, frame=3
seq N+4: NAV_LAND (21)            ← touchdown_point, frame=3
```

**理由**：与 Striker 的 `parse_preburned_mission()` 完全兼容（它只检查 LOITER_UNLIM 和 DO_LAND_START/NAV_LAND 的相对顺序），同时也是标准 ArduPlane AUTO 任务格式。

**替代方案考虑**：
- LOITER_TO_ALT 替代 LOITER_UNLIM → 不适用，Striker 期望 UNLIM 用于人工/GUIDED 接管
- 无 LOITER 直接降落 → 不兼容 Striker 流程

### D2: 高度参考框架 (frame)

**决定**：
- HOME (seq 0): `frame=0` (GLOBAL, AMSL)
- 所有其他航点: `frame=3` (GLOBAL_RELATIVE_ALT, 相对 HOME)

**理由**：与 `test_mission.waypoints` 样本一致，是 ArduPlane 固定翼最常用的高度模式。`field.json` 中的 `altitude_m`、`approach_alt_m` 都是相对地面高度的语义。

### D3: 纯函数 → logic.mjs

**决定**：所有序列化逻辑放入 `logic.mjs` 作为纯函数，`app.js` 仅调用并触发下载。

```
logic.mjs 新增：
  generateWaypointFile(fieldProfile, validation) → string (QGC WPL 110 文本)
  formatGeofencePoly(fieldProfile) → string (.poly 文本)
```

**理由**：保持 `logic.mjs` 无 DOM/AMap 依赖的架构约束，便于单元测试。

### D4: 盘旋点自定义交互

**决定**：在 `appState.fieldProfile` 中新增可选字段 `loiter_point: {lat, lon} | null`。
- `null` = 默认使用最后一个扫描航点
- 非 null = 用户自定义坐标

交互模式复用 `setDropPoint` 模式——新增一个 `setLoiterPoint` interactionMode，地图点击设置标记。

**理由**：复用已有的 `ensureMarker` + `handleMapClick` 分支模式，最小改动。

### D5: 导出 UI 布局

**决定**：将当前单个 "导出" 按钮扩展为按钮组：

```
[📦 导出航点 (.waypoints)] [🔲 导出围栏 (.poly)] [📄 导出配置 (field.json)]
```

**理由**：三个文件用途不同，用户可能只需要其中一个。不用 ZIP 打包是因为增加复杂度且用户经常只需航点文件。

### D6: scanPreview 坐标系处理

**决定**：`generateWaypointFile()` 内部对每个 scanPreview 点调用 `gcj02ToWgs84()`。

**理由**：`scanPreview` 由 `generateBoustrophedonScan()` 直接使用 `fieldProfile.boundary.polygon`（GCJ-02）生成，因此 scanPreview 中的坐标也是 GCJ-02。这与 `exportFieldProfile()` 处理 boundary 的逻辑一致。

## Risks / Trade-offs

- **[坐标转换遗漏]** → 任何漏转的点将导致 500m+ 偏移。缓解：`generateWaypointFile()` 内统一处理所有坐标转换，不依赖调用方转换。函数内部自包含 GCJ→WGS 逻辑。
- **[LOITER 点超出围栏]** → 用户自定义盘旋点可能放在围栏外。缓解：`validateFieldProfile()` 扩展校验，loiter_point 非 null 时检查 `pointInPolygon`。
- **[大量扫描航点]** → 密集扫描可能生成 200+ 航点，某些飞控有 766 或更低上限。缓解：validation 中添加 advisory 警告。
- **[field.json 结构变更]** → `loiter_point` 新字段会出现在 field.json 中。缓解：设为可选字段，现有 Striker 后端忽略未知字段。
