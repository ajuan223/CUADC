## ADDED Requirements

### Requirement: 能力注册表填充新能力
`REGISTRY.md` SHALL 注册以下新增或重命名的公共能力：`compute_fallback_drop_point`、`DropPointTracker`、`GpsDropPoint`、`MAVLinkConnection.flightmode`、`MissionContext.set_drop_point`、`MissionContext.update_mission_seq`。

#### Scenario: 新能力已注册
- **WHEN** `REGISTRY.md` 被读取
- **THEN** 表格中包含 `compute_fallback_drop_point`、`DropPointTracker`、`GpsDropPoint` 的条目
- **AND** 每个条目包含函数名、描述、所在模块、签名字段

#### Scenario: 已删除能力不在注册表中
- **WHEN** `REGISTRY.md` 被读取
- **THEN** 不包含 `generate_forced_strike_point`、`GpsTarget`、`TargetTracker`、`BallisticCalculator` 的条目
