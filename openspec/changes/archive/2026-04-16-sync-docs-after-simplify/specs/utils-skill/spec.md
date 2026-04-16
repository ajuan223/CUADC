## REMOVED Requirements

### Requirement: forced_strike_point validates safety buffer via boundary distance
**Reason**: `generate_forced_strike_point()` 函数和 `forced_strike_point.py` 模块已在 `simplify-mission-flow-drop-point` 变更中删除。强制投弹降级路径不再存在。
**Migration**: 不再需要此功能。

### Requirement: ApproachState passes velocity and wind to ballistic calculator
**Reason**: `ApproachState` 已删除，弹道解算不再在主流程中调用。视觉系统直接提供投弹点坐标，无需二次解算。
**Migration**: 不再需要此功能。

## ADDED Requirements

### Requirement: Fallback drop point computation
`compute_fallback_drop_point()` SHALL compute the geographic midpoint between the last scan waypoint and the landing reference point using geopy geodesic calculation.

#### Scenario: Midpoint between two known points
- **WHEN** `compute_fallback_drop_point(scan_end, landing_ref)` is called with two `GeoPoint` objects
- **THEN** the returned `(lat, lon)` SHALL be the geodesic midpoint between the two input points

#### Scenario: Deterministic output
- **WHEN** `compute_fallback_drop_point()` is called with the same inputs twice
- **THEN** the returned coordinates SHALL be identical
