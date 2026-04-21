## MODIFIED Requirements

### Requirement: Attack run geometry calculation
系统 SHALL 计算打击几何：给定投弹点坐标和进场航向，计算 approach 点（投弹点反向偏移 approach_distance_m）和 exit 点（投弹点正向偏移 exit_distance_m）。返回三元组 `(approach_lat_lon, target_lat_lon, exit_lat_lon)` 而非 mission items。

#### Scenario: 几何计算
- **WHEN** 调用 `compute_attack_geometry()` 提供 drop_lat, drop_lon, heading
- **THEN** SHALL 返回 approach / target / exit 三个 `(lat, lon)` 元组

#### Scenario: 进场航向使用 landing heading
- **WHEN** 调用计算时提供 `landing.heading_deg`
- **THEN** approach 点 SHALL 位于目标点反向 heading 方向 approach_distance_m 处

## REMOVED Requirements

### Requirement: Attack run mission generation
**Reason**: GUIDED 模式下不再需要生成 mission items。打击导航完全由 DO_REPOSITION 实现。
**Migration**: 使用 `compute_attack_geometry()` 获取坐标，通过 `FlightController.goto()` / `resend_position_target()` 导航。

### Requirement: Enroute state executes attack run
**Reason**: Enroute 状态已在之前重构中删除。由 GuidedStrikeState 替代。
**Migration**: 使用 `guided_strike.py`。

### Requirement: Release state confirms native release
**Reason**: 投弹由 GuidedStrikeState 程序化触发，release_monitor 简化为检查 `context.release_triggered` 标志。
**Migration**: `release_monitor.py` 不再依赖 servo_seq。

### Requirement: Landing state uses pre-uploaded mission
**Reason**: 降落段逻辑迁移到 `landing_monitor.on_enter()` 中执行 `MISSION_SET_CURRENT(landing_seq)` + `set_mode(AUTO)`。
**Migration**: 更新 `landing_monitor.py`。
