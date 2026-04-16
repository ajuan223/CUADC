## Context

SITL 联调已通过全链路验证（dry-run + non-dry-run），但代码中存在三个部署阻塞项：

1. `TakeoffState.arm()` 硬编码 `force=True`（param2=21196），跳过所有 ArduPlane pre-arm 检查。SITL 中必需，但真实部署时 GPS 未锁定也会强制起飞。
2. `landing_sequence.py` 为兼容 SITL 重上传场景将 DO_LAND_START 替换为 NAV_WAYPOINT，丢失了 ArduPlane 的 RALT（reverse altitude）和自动降落逻辑。
3. 缺少 MAVLink 路由层文档，MissionPlanner 无法与 companion 计算机同时连接飞控。

当前配置系统为 `StrikerSettings`（pydantic-settings），支持 code defaults → config.json → env vars 三层优先级。

## Goals / Non-Goals

**Goals:**
- arm force bypass 可通过配置控制，SITL 默认开、实飞默认关
- landing 序列恢复 DO_LAND_START 三项结构，SITL 场景可降级
- 提供清晰的路由层拓扑和部署文档

**Non-Goals:**
- 不做释放精度优化（acceptance radius / 进场速度调参）
- 不引入 mavlink-routerd 依赖，仅提供文档层面的路由指导
- 不修改 MAVLink 连接层的核心代码（connection.py 保持原样）

## Decisions

### D1: arm_force_bypass 作为 StrikerSettings 字段

在 `settings.py` 中新增 `arm_force_bypass: bool = False`。SITL 通过环境变量 `STRIKER_ARM_FORCE_BYPASS=1` 或 `config.json` 开启。

`TakeoffState.on_enter()` 从 `context.settings.arm_force_bypass` 读取并传给 `flight_controller.arm()`。

**替代方案:** 在 field.json 中配置。否决——这是系统级行为，不属于场地配置。

### D2: landing_use_do_land_start 作为 field profile 配置

在 `field_profile.py` 的 `LandingConfig` 中新增 `use_do_land_start: bool = True`。

`landing_sequence.py` 根据 `landing.use_do_land_start` 决定：
- `True`: DO_LAND_START + approach + NAV_LAND（3 项，固定翼最优）
- `False`: approach (NAV_WAYPOINT) + NAV_LAND（2 项，SITL 降级）

SITL 的 `field.json` 中设为 `false`，真实场地默认 `true`。

**替代方案:** 全局 settings 控制。否决——landing 行为与场地和飞控固件相关，应在 field profile 中配置。

### D3: MAVLink 路由层仅提供文档

不引入新的 Python 依赖或路由进程管理。在部署文档中说明 MAVProxy / mavlink-routerd 拓扑和配置命令。现有 SITL 联调文档已包含 MAVProxy 桥接拓扑，实飞部署拓扑类似。

## Risks / Trade-offs

- **[SITL 回归]** 恢复 DO_LAND_START 后，SITL 中 enroute 重上传场景可能再次失败 → 通过 `use_do_land_start=false` 在 SITL field profile 中降级，保持 SITL 通过
- **[arm 失败]** 关闭 force bypass 后，pre-arm 检查不通过时无法起飞 → 这是预期行为，实飞时必须保证传感器健康
- **[配置不一致]** SITL field 配了 `false` 而实飞忘记配 `true` → 默认值 `True` 保证实飞安全
