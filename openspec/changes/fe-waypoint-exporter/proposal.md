## Why

Field Editor 已经拥有完整的牛耕扫描路径生成、起降进近推导、边界多边形编辑能力，但当前只导出 `field.json` 配置文件。实际的飞控航点任务需要在 Mission Planner 中手动重新绘制，造成重复劳动且容易引入不一致。将 FE 升级为直接导出 ArduPilot/Mission Planner 兼容的 `.waypoints` 文件（QGC WPL 110 格式），消除中间手工步骤。

## What Changes

- **新增 `.waypoints` 导出**：将 FE 已有的 `scanPreview`、`derivedApproach`、`derivedTakeoff` 组装为完整的 QGC WPL 110 任务序列（HOME → TAKEOFF → Scan WPs → LOITER_UNLIM → DO_LAND_START → Approach → LAND），直接可烧录飞控
- **新增 `.poly` geofence 导出**：将边界多边形导出为 Mission Planner 兼容的 geofence 围栏文件
- **新增盘旋点自定义交互**：LOITER_UNLIM 默认放在最后一个扫描航点，但用户可通过地图工具自定义位置
- **保留 `field.json` 导出**：现有 JSON 导出作为并行选项保留，Striker 后端仍可使用
- **保留 `attack_run` 字段**：UI 上保留编辑能力但不写入 `.waypoints`；仅保留在 `field.json` 中

## Capabilities

### New Capabilities
- `waypoint-file-export`: 将 FE 规划数据序列化为 QGC WPL 110 格式的 `.waypoints` 文件，含完整 MAV_CMD 任务序列
- `geofence-poly-export`: 将边界多边形导出为 Mission Planner `.poly` geofence 文件
- `loiter-point-interaction`: 地图上交互式设置/拖拽 LOITER_UNLIM 盘旋等待点

### Modified Capabilities
- `field-editor-planning-workflow`: 导出按钮区域从单一 "导出 field.json" 变为三按钮（.waypoints / .poly / field.json）

## Impact

- **`logic.mjs`**：新增 `generateWaypointFile()`、`formatGeofencePoly()` 纯函数
- **`app.js`**：新增导出处理函数、盘旋点交互模式、`downloadFile()` MIME type 参数化
- **`index.html`**：导出工具栏新增按钮
- **`styles.css`**：可能微调按钮布局
- **坐标系红线**：所有写入 `.waypoints` 和 `.poly` 的坐标必须经过 `gcj02ToWgs84()` 转换
- **Striker 后端**：无变更，`field.json` 导出保持兼容
