# Striker 能力注册表

> 本表记录项目中所有可复用的通用函数和类实现。
> 新增通用函数时请追加到表格末尾，函数签名变更时请同步更新。

| 函数名 | 描述 | 所在模块 | 签名 |
|--------|------|---------|------|
| `compute_fallback_drop_point` | 计算扫场终点与降落参考点的地理中点（geopy geodesic） | `src/striker/utils/` | `compute_fallback_drop_point(scan_end_point: GeoPoint, landing_reference_point: GeoPoint) -> tuple[float, float]` |
| `DropPointTracker` | 投弹点跟踪器，滑动窗口中值滤波消除高频抖动 | `src/striker/vision/` | `DropPointTracker(window_size: int, stale_timeout_s: float)` |
| `GpsDropPoint` | 投弹点坐标数据类（lat/lon/置信度/时间戳） | `src/striker/vision/` | `GpsDropPoint(lat: float, lon: float, confidence: float, timestamp: float)` |
| `MAVLinkConnection.flightmode` | 当前飞控模式名（pymavlink auto-decoded，如 MANUAL/AUTO/GUIDED/FBWA） | `src/striker/comms/` | `property -> str` |
| `MissionContext.set_drop_point` | 设置活跃投弹点及其来源标注 | `src/striker/core/` | `set_drop_point(lat: float, lon: float, source: str) -> None` |
| `MissionContext.update_mission_seq` | 更新当前任务序列号（MISSION_CURRENT / MISSION_ITEM_REACHED） | `src/striker/core/` | `update_mission_seq(seq: int) -> None` |
| `validate_gps` | 校验 GPS 坐标是否在有效范围内 | `src/striker/vision/` | `validate_gps(lat: float, lon: float) -> None` |
| `haversine_distance` | 两点间 GPS 距离计算（haversine 公式） | `src/striker/utils/geo.py` | `haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float` |
| `point_in_polygon` | 判断点是否在多边形内部 | `src/striker/utils/` | `point_in_polygon(lat: float, lon: float, polygon: list[tuple[float, float]]) -> bool` |
