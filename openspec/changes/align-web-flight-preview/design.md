## Context

Web 场地编辑器 (`src/field_editor/`) 和 Python 后端 (`src/striker/flight/`) 各自实现了飞行路径算法。JS 端的 `generateBoustrophedonScan` 和 `deriveTakeoffPreview` 与 Python 端的 `generate_boustrophedon_scan` 和 `generate_takeoff_geometry` 存在算法漂移。同时 web 编辑器只画了部分飞行阶段，缺少起飞路径和段间连接。

## Goals / Non-Goals

**Goals:**
- JS 扫描路径算法与 Python 1:1 对齐（inset + midpoint check）
- 修复 climbout 距离 bug（1.0× → 0.5×）
- 在地图上画出完整飞行链路：起飞 → 扫描 → 降落，含段间连接
- 投弹预览标注为静态预览

**Non-Goals:**
- 不修改 Python 后端算法（Python 是 source of truth）
- 不重构 web 编辑器架构或模块划分
- 不实现动态投弹路径预览（实际目标由视觉系统实时决定）
- 不修改 coordinate_system 或 GCJ-02/WGS84 转换逻辑

## Decisions

### D1: 直接在 logic.mjs 中补齐缺失逻辑

在 `generateBoustrophedonScan` 的 for 循环内，紧跟 intersections 配对之后、方向交替之前，插入 midpoint check 和 inset 计算。这与 Python `mission_geometry.py:287-298` 的位置和逻辑一致。

**替代方案**：抽取共享算法模块。拒绝理由——两端语言不同（JS vs Python），共享模块无法实现；且改动范围应最小化。

### D2: 段间连接用独立 overlay 管理

新增 `takeoffPathLine`、`missionChainLine` overlay 到 `mapState.overlays`，在 `renderOverlays` 中统一调用。使用灰色虚线（`strokeColor: "#94a3b8"`, `strokeStyle: "dashed"`）与实际飞行路径（绿色实线）区分。

**替代方案**：将连接线合并到 scan polyline。拒绝理由——语义不同（连接线不是航点），颜色/样式不同，分开管理更清晰。

### D3: 起飞路径用实线、与跑道同色系

起飞 start → climbout 用 `#f59e0b`（amber）实线，与跑道红色区分但保持"地面阶段"色系。起点/终点不加 marker（已有 deriveTakeoffPreview 的数据在 landingApproachSummary 中展示）。

### D4: 投弹预览标注用 HTML label

在 attack run overlay 的 label 区域加 "(预览)" 后缀。不引入新 UI 组件或 tooltip 库。

## Risks / Trade-offs

- [inset/midpoint 对齐后 scan 航点数可能略微减少] → 符合实际飞行行为，可接受；inset 仅 1-5 米，视觉上无感知
- [段间连接线在 scan 为空时不画] → 自然退化为无连接线，不影响其他 overlay
- [climbout 距离修正改变了预览中起飞终点的位置] → 修正了 bug，之前是错误的
