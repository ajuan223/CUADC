## Context

当前 enroute 状态使用 GUIDED 模式 + DO_REPOSITION 命令飞向投弹点。ArduPlane 固定翼的 GUIDED 模式导航调用 `update_loiter()`，飞机到达目标后自动进入盘旋（loiter radius ~50-80m），导致释放距离误差约 97m。

ArduPlane AUTO 模式的 NAV_WAYPOINT 使用 `update_waypoint()` 执行直线段飞行，`past_interval_finish_line()` 检测航点通过后立即推进到下一航点。DO_SET_SERVO 作为 DO 类型命令在两个 NAV 命令之间执行——当 target 航点完成时立即触发舵机。这是 ArduPlane 原生的投放机制，在 Kingaroy 大型任务等实战示例中已有应用。

经过 ArduPlane 源码追踪（`mode_auto.cpp`, `commands_logic.cpp:634-697`, `AP_Mission.cpp:2055-2138`），确认：
- AUTO 模式 NAV_WAYPOINT 直线穿点、不停留不盘旋
- DO 命令在前一个 NAV 完成时立即执行
- 释放精度受 WP_RADIUS 参数控制（默认 ~30m）
- `param2` 可自定义 acceptance radius 以提升精度

## Goals / Non-Goals

**Goals:**
- 将 enroute 飞行策略从 GUIDED 盘旋替换为 AUTO 攻击跑直线穿点
- 利用 ArduPlane 原生 DO_SET_SERVO 任务项实现飞控级释放触发
- 释放精度从 ~97m 提升到 ~30m（默认 WP_RADIUS）
- 保留 dry_run 模式兼容性
- enroute 状态代码从"实时控制"简化为"上传+监控"

**Non-Goals:**
- 不引入弹道解算、风速补偿投放等高级投放优化
- 不修改 ArduPlane 固件参数（WP_RADIUS 等保持默认）
- 不实现多轮攻击或重新攻击逻辑
- 不在本次变更中修改安全检查、地理围栏或电池监控逻辑
- 不改变起飞、扫场、降落阶段的行为

## Decisions

### 1. 使用 AUTO 模式临时任务替代 GUIDED 模式
攻击跑通过上传一个临时 AUTO 任务实现，包含 approach → target → exit 三个 NAV_WAYPOINT。飞机在 AUTO 模式下直线穿过所有航点，不盘旋不停留。

**Alternatives considered:**
- **GUIDED + heading hold**：需要 `AP_PLANE_OFFBOARD_GUIDED_SLEW_ENABLED`，兼容性不确定，释放仍需 companion 控制
- **ArduPlane Lua scripting**：灵活但引入 scripting 依赖，增加调试复杂度

### 2. DO_SET_SERVO 嵌入任务项实现原生释放
在 target 和 exit 航点之间嵌入 DO_SET_SERVO 命令。ArduPlane 在 target 航点完成时（`verify_nav_wp` 返回 true）立即执行 DO_SET_SERVO，无 MAVLink 往返延迟。

**Alternatives considered:**
- **Companion computer 监控距离触发**：可行但有 ~50-100ms 延迟（20m/s 下 = 2m 误差），且增加 enroute 代码复杂度
- **MAV_CMD_NAV_PAYLOAD_PLACE**：主要用于 VTOL/quadplane，不适用于固定翼

### 3. dry_run 模式条件性排除 DO_SET_SERVO
当 `dry_run=True` 时不在任务中嵌入 DO_SET_SERVO，由 RELEASE 状态通过 companion computer 的 dry_run 释放控制器处理。当 `dry_run=False` 时嵌入任务项，释放完全由飞控处理。

### 4. 攻击跑几何解算：逆风优先
approach heading 按以下优先级确定：
1. 风场数据可用且风速 > 2m/s → 逆风进场（`wind_direction + 180°`）
2. 有当前位置 → 从当前位置直飞目标的 bearing
3. 兜底 → 场地 landing heading 的反方向

approach 距离和 exit 距离通过 field profile 配置（默认 200m）。

### 5. 攻击跑任务包含 landing items
attack+landing 作为一个完整任务上传，避免释放后重新上传降落任务。任务结构：
```
seq 0: dummy HOME
seq 1: NAV_WAYPOINT(approach)
seq 2: NAV_WAYPOINT(target)
seq 3: DO_SET_SERVO (non-dry only)
seq 4: NAV_WAYPOINT(exit)
seq 5: DO_LAND_START
seq 6: NAV_WAYPOINT(landing_approach)
seq 7: NAV_LAND(touchdown)
```

### 6. enroute 状态监控 mission_current_seq
enroute 不再监控 GPS 距离，改为监控 ArduPlane 的 MISSION_CURRENT 遥测。当 `mission_current_seq >= target_seq + 1` 时，表示 target 航点已完成（DO_SET_SERVO 已执行），触发状态转换到 RELEASE。

## Risks / Trade-offs

- **[WP_RADIUS 精度依赖]** → 默认 ~30m，可通过 param2 (acceptance radius) 调优。需在 SITL 中验证实际值 → 首次联调记录实际释放距离
- **[approach/exit 点可能出界]** → 200m offset 可能超出 geofence boundary → 不在 mission upload 层做边界检查，由操作员在 field config 中合理设置 approach_distance_m
- **[MISSION_SET_CURRENT 时序]** → 切换 AUTO 后需等待模式生效再发 MISSION_SET_CURRENT → enroute on_enter 中加入短暂延迟
- **[dry_run 模式 companion 释放延迟]** → 仅影响 dry_run 模式，真实模式由飞控原生处理 → 可接受
- **[风场数据不可用]** → 降级到"从当前位置直飞"策略 → 已设计 fallback 链
