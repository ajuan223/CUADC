## Why

当前 enroute 状态使用 GUIDED 模式的 DO_REPOSITION 命令飞向投弹点，ArduPlane 固定翼在到达目标后会进入 loiter 盘旋（radius ~50-80m），导致释放距离误差约 97m。真实打击任务采用直线攻击跑（attack run）策略——沿预定航向直线穿过目标点释放载荷。ArduPlane AUTO 模式原生支持直线穿点飞行和任务内嵌 DO_SET_SERVO 自动释放，无需 companion computer 实时控制释放时机，可显著提升精度并简化代码。

## What Changes

- **替换 enroute 飞行策略**：从 GUIDED+DO_REPOSITION（盘旋接近）改为 AUTO 模式临时任务（直线攻击跑）
- **新增攻击跑几何解算**：根据风场数据或当前位置计算 approach / exit 航点，偏好逆风进场
- **原生 DO_SET_SERVO 释放**：在任务序列中嵌入 DO_SET_SERVO 命令项，由 ArduPlane 飞控在到达投弹点时自动触发舵机释放
- **enroute 状态重写**：从"实时 GUIDED 控制"变为"上传任务后监控 mission progress"
- **release 状态简化**：从"触发释放"变为"确认释放已执行"（ArduPlane 已通过任务项处理）
- **landing 状态简化**：攻击跑任务已包含 landing items，无需重新上传降落任务

## Capabilities

### New Capabilities
- `attack-run`: 攻击跑飞行策略——计算 approach/target/exit 三航点几何，生成临时 AUTO 任务，利用 ArduPlane 原生直线穿点导航和任务内嵌 DO_SET_SERVO 实现精确投放

### Modified Capabilities
- `field-profile`: 新增攻击跑配置参数（approach_distance_m, exit_distance_m, release_acceptance_radius_m）

## Impact

- **核心文件**：`enroute.py`（重写）、`navigation.py`（新增 make_do_set_servo / build_attack_run_mission）、`mission_upload.py`（新增 upload_attack_mission）
- **次要文件**：`release.py`（简化）、`landing.py`（简化）、`context.py`（可能新增 attack_run 元数据）
- **配置文件**：field profile JSON 新增 attack_run 配置节
- **MAVLink 交互**：从 COMMAND_LONG (DO_REPOSITION) 切换到 MISSION_ITEM_INT (NAV_WAYPOINT + DO_SET_SERVO)
- **SITL 验证**：需验证 WP_RADIUS 默认值下的实际释放精度，以及 DO_SET_SERVO 在任务中的执行时机
- **dry_run 兼容**：任务中条件性排除 DO_SET_SERVO，由 companion computer 的 dry_run 逻辑接管释放
