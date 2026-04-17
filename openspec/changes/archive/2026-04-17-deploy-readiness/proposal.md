## Why

SITL 联调已通过，但代码中有三个阻碍真实部署的问题：arm `force=True` 跳过所有安全检查（生产环境危险）、landing 序列为兼容 SITL 去掉了 DO_LAND_START（丢失了固定翼最优降落逻辑）、以及缺少 MAVLink 路由层支持（MissionPlanner 无法与 companion 共存）。需要在实飞前修复这些。

## What Changes

- **arm force 可配置化**: 将 `force=True` 硬编码改为通过 `StrikerSettings` 配置（`arm_force_bypass: bool`），SITL 默认 `True`，实飞默认 `False`
- **恢复 DO_LAND_START**: landing 序列恢复使用 DO_LAND_START + approach + NAV_LAND 三项结构，仅在 SITL 重上传场景下提供降级选项
- **MAVLink 路由层**: 在启动文档和配置中加入 MAVProxy/mavlink-routerd 路由拓扑，支持 MissionPlanner 和 striker 同时连接飞控

## Capabilities

### New Capabilities
- `mavlink-routing`: MAVLink 路由层配置与拓扑文档，支持 MissionPlanner/companion/GCS 多端共存

### Modified Capabilities
- `config-system`: 新增 `arm_force_bypass` 和 `landing_use_do_land_start` 配置项
- `field-profile`: landing 序列生成逻辑恢复 DO_LAND_START，保留 SITL 降级选项

## Impact

- `src/striker/config/settings.py`: 新增配置字段
- `src/striker/core/states/takeoff.py`: arm 调用使用 settings 中的 force 配置
- `src/striker/flight/landing_sequence.py`: 恢复 DO_LAND_START，条件降级
- `src/striker/flight/navigation.py`: `build_attack_run_mission` 传递 landing 模式参数
- `data/fields/sitl_default/field.json`: 新增 `landing.use_do_land_start: false`（SITL 降级）
- `docs/attack_run_dryrun_report.md`: 更新部署拓扑说明
