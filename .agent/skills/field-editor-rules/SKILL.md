# Field Editor Web 编码规范

本 Skill 约束 `src/field_editor/` 目录下所有代码。Field Editor 是基于 AMap（高德地图）的 Web 场地编辑器，使用 GCJ-02 坐标系进行地图交互，导出为 WGS84。

> 场地数据在运行时使用 WGS84，Web 编辑器内部使用 GCJ-02。两者之间的转换是本模块最关键的约束。

## 核心约束：坐标系转换

### GCJ-02 / WGS84 双坐标系统

| 阶段 | 坐标系 | 说明 |
|------|--------|------|
| Web 编辑器内部 | GCJ-02 | AMap 原生坐标系，所有地图交互使用此坐标系 |
| 导出 field.json | WGS84 | 标准地理坐标系，运行时使用 |
| 导入 field.json | 取决于文件标注 | `coordinate_system` 字段标识 |
| 运行时 (Striker) | WGS84 | 飞控、导航、安全围栏全部使用 WGS84 |

### 红线：每一个地图交互坐标都必须经过转换

**导出时（`exportFieldProfile`）：**
- `boundary.polygon` — 每个顶点必须 `gcj02ToWgs84()`
- `landing.touchdown_point` — 必须 `gcj02ToWgs84()`
- `attack_run.fallback_drop_point` — 必须 `gcj02ToWgs84()`
- **任何未来新增的地图交互点/线/面** — 必须 `gcj02ToWgs84()`

**导入时（`importFieldProfile`）：**
- 当源文件为 WGS84 时，所有地理坐标必须 `wgs84ToGcj02()` 转换到 GCJ-02
- 当源文件为 GCJ-02 时，直接使用
- 转换范围必须覆盖所有地理坐标字段，不得遗漏任何一个

**新增地图交互功能时（checklist）：**
1. 在 `exportFieldProfile` 中添加 `gcj02ToWgs84()` 转换
2. 在 `importFieldProfile` 的 WGS84 分支中添加 `wgs84ToGcj02()` 转换
3. 在 Web 端显示时使用 GCJ-02（AMap 原生）
4. 确认 `logic.mjs` 中的 `createDefaultFieldProfile()` 使用 `GCJ-02` 标识

## 架构约束

### 文件结构

| 文件 | 职责 |
|------|------|
| `index.html` | UI 布局、表单、工具栏按钮 |
| `app.js` | 主应用逻辑、AMap 交互、overlay 管理、事件绑定 |
| `logic.mjs` | 纯计算逻辑：坐标转换、几何算法、校验、序列化 |
| `interaction_state.mjs` | 绘图会话状态管理 |
| `styles.css` | 样式 |
| `config.js` | AMap 凭据配置 |

### 依赖方向

- `app.js` 可依赖: `logic.mjs`, `interaction_state.mjs`, AMap API
- `logic.mjs` 不依赖任何 DOM 或 AMap API — 纯计算
- `interaction_state.mjs` 不依赖 DOM — 纯状态
- `app.js` 通过 AMap API 进行地图交互

### 新增地图交互功能模式

参考现有跑道设置 (`setRunway`) 的模式：
1. `index.html` — 在工具栏添加按钮
2. `app.js` — DOM 引用、interactionMode 状态、`handleMapClick` 分支、overlay 渲染
3. `logic.mjs` — 如需新计算函数则添加（坐标转换、几何推导）
4. 导出/导入 — 添加对应的坐标转换逻辑

### Overlay 管理

- 所有地图覆盖物存储在 `mapState.overlays` 对象中
- 使用 `ensureMarker()` 创建/更新可拖动标记
- 使用 `removeOverlay()` 清理
- `renderOverlays()` 统一渲染所有覆盖物

## 禁止模式

- **禁止**在 `exportFieldProfile` 中遗漏任何地理坐标字段的 GCJ-02→WGS84 转换 — 这是导致运行时位置偏移数百米的致命 bug（GCJ-02/WGS84 在中国偏移可达 500m+）
- **禁止**在 `importFieldProfile` 中遗漏 WGS84→GCJ-02 转换
- **禁止**在 `logic.mjs` 中引用 DOM 或 AMap API
- **禁止**硬编码坐标 — 默认值使用 `DEFAULT_CENTER`
- **禁止**跳过 `validateFieldProfile()` 校验 — 导出前必须通过校验

## 历史教训

- 2026-04-18: `fallback_drop_point` 导出时未转换坐标系，导致运行时投弹点偏移约 500m，触发 geofence emergency。boundary 和 touchdown 均已转换，唯独遗漏了 drop point。
