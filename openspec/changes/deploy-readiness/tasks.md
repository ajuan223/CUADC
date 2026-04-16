## 1. 配置接口

- [x] 1.1 `settings.py` 新增 `arm_force_bypass: bool = False` 字段，支持 `STRIKER_ARM_FORCE_BYPASS` 环境变量覆盖
- [x] 1.2 `field_profile.py` 的 `LandingConfig` 新增 `use_do_land_start: bool = True` 字段

## 2. arm force 配置化

- [x] 2.1 `takeoff.py` 的 `on_enter()` 从 `context.settings.arm_force_bypass` 读取 force 参数，传给 `flight_controller.arm(force=...)`

## 3. 恢复 DO_LAND_START

- [x] 3.1 `landing_sequence.py` 根据 `field_profile.landing.use_do_land_start` 分支生成：`True` → DO_LAND_START + approach + NAV_LAND (3项)；`False` → approach + NAV_LAND (2项，SITL降级)
- [x] 3.2 `data/fields/sitl_default/field.json` landing 节新增 `"use_do_land_start": false`

## 4. MAVLink 路由层文档

- [x] 4.1 更新 `docs/attack_run_dryrun_report.md` 新增实飞部署路由拓扑节，包含 SITL 和真实部署两种 MAVProxy/mavlink-routerd 配置命令

## 5. 验证

- [x] 5.1 SITL 验证：`STRIKER_ARM_FORCE_BYPASS=true` + `use_do_land_start=false` 下全链路通过
- [x] 5.2 检查 `arm_force_bypass=false` 时 arm 调用使用 `param2=0`（无 bypass）
