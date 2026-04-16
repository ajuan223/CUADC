## Context

`attack-run-precision-drop` 变更已完成以下代码修改：
- `enroute.py`：从 GUIDED+DO_REPOSITION 重写为 AUTO 攻击跑策略（upload attack mission → switch AUTO → monitor mission_current_seq）
- `navigation.py`：新增 `make_do_set_servo()` 和 `build_attack_run_mission()` 生成 approach/target/exit + DO_SET_SERVO + landing 任务序列
- `mission_upload.py`：新增 `upload_attack_mission()` 上传完整攻击跑+降落任务
- `release.py`：适配原生释放（dry_run=False 时 DO_SET_SERVO 已由飞控执行）
- `landing.py`：简化为 `mission_set_current` 到预上传的 landing start index
- `field_profile.py`：新增 `AttackRunConfig` 数据模型
- `field.json`：已添加 `attack_run` 配置节（approach/exit 各 200m）

SITL 基础设施（参考 `sitl-dryrun-debug-spec`）：
- `sim_vehicle.py -v ArduPlane -L Zijingang` 启动 SITL + MAVProxy，UDP 14550 输出
- `scripts/mock_vision_server.py` 发送 mock 投弹点坐标
- `scripts/dryrun.sh` 自动化联调脚本
- Zijingang 位置（30.265, 120.095）已配置

当前 field.json boundary：lat 30.2600-30.2700, lon 120.0900-120.1000（约 1.1km × 0.8km）。attack_run approach/exit 各 200m offset，在 1km 级别场地内可行，但投弹点靠近 boundary 边缘时 approach/exit 点可能出界。

## Goals / Non-Goals

**Goals:**
- 在 SITL 中完成 attack-run-precision-drop 全链路联调：init → preflight → takeoff → scan → enroute(attack run) → release → landing → completed
- 验证攻击跑几何解算（approach heading、approach/exit 坐标）在 SITL 中正确
- 验证 AUTO 模式攻击跑任务上传、MISSION_SET_CURRENT、mission_current_seq 推进
- 验证 DO_SET_SERVO 在任务中的执行时机（non-dry-run 模式）
- 验证 release 状态在 dry-run 和 non-dry-run 模式下的行为
- 验证 landing 状态使用预上传 landing 序列正常降落
- 记录实际释放精度（与 WP_RADIUS 的关系）
- 更新 dry-run 联调策略和 debug guide 以覆盖攻击跑特有故障模式

**Non-Goals:**
- 不修改攻击跑核心业务代码（enroute.py、navigation.py 等）——代码修改属 `attack-run-precision-drop` 变更
- 不修改 SITL 环境基础配置（位置、MAVProxy 安装等）——已在 `sitl-dryrun-debug-spec` 完成
- 不做弹道解算或风速补偿验证
- 不搭建 CI 环境或自动化回归测试
- 不修改安全检查、地理围栏或电池监控逻辑

## Decisions

### 1. 联调策略：分阶段验证攻击跑链路
延续 `sitl-dryrun-debug-spec` 的分阶段验证方法论，但 Phase 4（enroute）从 GUIDED 验证改为 attack run 验证。新增验证点：
- enroute on_enter：attack mission upload 成功、AUTO 模式切换、MISSION_SET_CURRENT 到 approach seq
- enroute execute：mission_current_seq 从 approach 推进到 target 再到 exit
- release：dry-run 模式 companion 释放；non-dry-run 模式飞控原生 DO_SET_SERVO
- landing：mission_set_current 到 landing start index 成功

### 2. Mock 投弹点坐标选择
mock_vision_server 发送投弹点坐标需满足：approach/exit 点（各 200m offset）在 field boundary 内。选择场区中心附近坐标（如 30.2650, 120.0950）作为默认 mock 投弹点，确保 approach/exit 不出界。

**边缘情况**：投弹点靠近 boundary 时 200m offset 可能出界。enroute 代码不做出界检查（由操作员在 field config 中合理配置），但 SITL 联调应验证正常 case 和记录边界 case 行为。

### 3. 精度评估方法
在 non-dry-run 模式下，通过 MISSION_ITEM_REACHED 消息记录 target waypoint 完成时刻的 GLOBAL_POSITION_INT 与目标坐标的 haversine 距离，作为实际释放精度。与 WP_RADIUS（默认 ~30m）对比。

### 4. Dry-run 模式 vs Non-dry-run 模式双路径验证
- `--dry-run` 模式：DO_SET_SERVO 不嵌入任务，release 由 companion computer 处理，只打日志
- non-dry-run 模式：DO_SET_SERVO 嵌入任务，由飞控在 target waypoint 完成时执行，需验证舵机 PWM 信号

SITL 中可验证两种模式，但舵机信号需要通过 MAVLink SERVO_OUTPUT_RAW 消息观测。

### 5. 攻击跑故障模式扩展
在现有四层 debug 模型基础上新增攻击跑特有故障模式：
- **M-06: MISSION_SET_CURRENT 无效** — AUTO 模式下 set current 失败
- **M-07: mission_current_seq 不推进** — 任务上传成功但 seq 不变化
- **M-08: DO_SET_SERVO 未执行** — target waypoint 完成但舵机未触发
- **B-05: Attack run approach/exit 出界** — 投弹点太靠近 boundary

## Risks / Trade-offs

- **[mission_current_seq 轮询间隔]** → enroute execute() 以 ~4Hz 轮询 mission_current_seq，可能错过快速推进。SITL 中 attack run 飞行速度约 20m/s，approach 到 exit 距离 400m，约 20 秒完成，足够观测
- **[SITL 风场模拟]** → SITL 默认无风或微风。攻击跑逆风进场逻辑在 SITL 中可能降级到直飞 bearing fallback。可通过 SIM_WIND_DIR/SIM_WIND_SPD 参数模拟风场验证逆风逻辑
- **[WP_RADIUS 在 SITL 中的默认值]** → ArduPlane 默认 WP_RADIUS 约 30m，SITL 中行为应一致。需记录实际值和通过距离
- **[field.json attack_run 配置合理性]** → approach_distance_m=200 在 1km 场地中可行，但如果投弹点在 boundary 边缘，approach/exit 可能出界。SITL 中默认 mock 投弹点选在中心附近规避此问题
- **[dry-run 联调经验复用]** → `sitl-dryrun-debug-spec` 已有一次全链路 dry-run 经验（2026-04-16），SITL 环境、mock server、联调脚本均已有基础，本次联调应能快速推进
