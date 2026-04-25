## 1. logic.mjs 核心导出函数

- [x] 1.1 新增 `generateWaypointFile(fieldProfile, validation)` 纯函数，返回 QGC WPL 110 格式字符串
- [x] 1.2 实现 `formatQgcWplLine(item)` 内部辅助函数，将单个任务项格式化为 tab 分隔行
- [x] 1.3 实现完整任务序列组装：HOME → TAKEOFF → Scan WPs → LOITER_UNLIM → DO_LAND_START → Approach → LAND
- [x] 1.4 确保所有坐标通过 `gcj02ToWgs84()` 转换（scanPreview、derivedApproach、touchdown_point、loiter_point）
- [x] 1.5 新增 `formatGeofencePoly(fieldProfile)` 纯函数，返回 `.poly` 格式字符串（顶点数 + WGS84 坐标行）
- [x] 1.6 在 export 列表中新增 `generateWaypointFile` 和 `formatGeofencePoly`

## 2. loiter_point 数据模型

- [x] 2.1 在 `createDefaultFieldProfile()` 中新增 `loiter_point: null` 字段
- [x] 2.2 在 `exportFieldProfile()` 中处理 `loiter_point` 的 GCJ-02→WGS84 转换
- [x] 2.3 在 `importFieldProfile()` 中处理 `loiter_point` 的 WGS84→GCJ-02 转换（可选字段）
- [x] 2.4 在 `mergeImportedProfile()` 中合并 `loiter_point` 字段
- [x] 2.5 在 `validateFieldProfile()` 中新增盘旋点围栏校验（loiter_point 非 null 时检查 pointInPolygon）

## 3. app.js 盘旋点交互

- [x] 3.1 新增 `setLoiterPoint` interactionMode，复用 `handleMapClick` 分支模式
- [x] 3.2 新增 `loiterPointMarker` overlay，使用 `ensureMarker()` 创建可拖动标记
- [x] 3.3 实现拖拽回调 `syncMarkersFromMap("loiterPointMarker")`，更新 `fieldProfile.loiter_point`
- [x] 3.4 在 `renderOverlays()` 中调用新增的 `renderLoiterPoint()` 函数

## 4. app.js 导出逻辑

- [x] 4.1 修改 `downloadFile()` 函数，添加 `mimeType` 可选参数（默认 `application/json`）
- [x] 4.2 新增 `handleExportWaypoints()` 函数：调用 `generateWaypointFile()` 并下载 `.waypoints` 文件
- [x] 4.3 新增 `handleExportGeofence()` 函数：调用 `formatGeofencePoly()` 并下载 `.poly` 文件
- [x] 4.4 保留现有 `handleExport()` 作为 field.json 导出（重命名为 `handleExportFieldJson()`）

## 5. index.html UI 变更

- [x] 5.1 将单个 `#export-button` 替换为三个导出按钮：`#export-waypoints-button`、`#export-geofence-button`、`#export-fieldjson-button`
- [x] 5.2 新增 "设置盘旋点" 工具栏按钮 `#set-loiter-button`
- [x] 5.3 更新按钮文案和图标

## 6. app.js 事件绑定与 DOM 引用

- [x] 6.1 更新 `dom` 对象，新增三个导出按钮和盘旋点按钮引用
- [x] 6.2 在 `wireEventHandlers()` 中绑定新的导出按钮事件
- [x] 6.3 在 `wireEventHandlers()` 中绑定盘旋点设置按钮事件
- [x] 6.4 更新 `renderValidation()` 中的按钮 disabled 逻辑：.waypoints 和 field.json 按 blocking 控制，.poly 按边界顶点数控制

## 7. 验证

- [x] 7.1 在浏览器中测试：创建完整 field profile → 导出 `.waypoints` → 在 Mission Planner 中导入验证
- [x] 7.2 验证 `.poly` 文件可在 Mission Planner 中导入为 geofence
- [x] 7.3 验证自定义 loiter_point 的导入/导出/校验循环
- [x] 7.4 验证 field.json 导出功能不受影响（回归测试）
